"""
Advisor agent for generating operational briefs.

This module generates plain-language operational briefs from detected anomalies
using IBM Granite LLM via watsonx API. It orchestrates prompt building,
LLM inference, and response formatting.
"""

import pandas as pd
from typing import Dict, Any, Optional, List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.logger import setup_logger
from src.utils.config_loader import get_config_value
from src.agents.advisor.watsonx_client import initialize_client, WatsonxClient
from src.agents.advisor.prompt_templates import (
    build_prompt,
    build_batch_prompt,
    format_anomaly_data,
    get_template,
    ANOMALY_BRIEF_TEMPLATE,
    BATCH_ANOMALIES_TEMPLATE
)

logger = setup_logger(__name__)


def generate_ops_brief(
    anomaly_data: Dict[str, Any],
    client: Optional[WatsonxClient] = None,
    template: Optional[str] = None,
    include_context: bool = True,
    **kwargs
) -> str:
    """
    Generate operational brief from anomaly data.
    
    This is the main function for generating a single operational brief.
    It handles prompt construction, LLM inference, and response formatting.
    
    Args:
        anomaly_data: Dictionary containing anomaly information
        client: Initialized WatsonxClient (creates new if None)
        template: Custom prompt template (uses default if None)
        include_context: Whether to include contextual information
        **kwargs: Additional parameters for prompt building and generation
        
    Returns:
        Plain-language operational brief text
    """
    logger.info(f"Generating operational brief for anomaly at {anomaly_data.get('timestamp', 'unknown')}")
    
    # Initialize client if not provided
    if client is None:
        logger.debug("Initializing watsonx client")
        client = initialize_client()
    
    # Use default template if not provided
    if template is None:
        template = ANOMALY_BRIEF_TEMPLATE
    
    # Enrich anomaly context
    enriched_anomaly = analyze_anomaly_context(anomaly_data)
    
    # Build prompt
    logger.debug("Building prompt from template")
    prompt = build_prompt(
        enriched_anomaly,
        template=template,
        include_context=include_context,
        **kwargs
    )
    
    # Generate text using LLM
    logger.info("Calling LLM for brief generation")
    try:
        # Get generation parameters from config
        temperature = kwargs.get('temperature', get_config_value('advisor.temperature', 0.7))
        max_tokens = kwargs.get('max_tokens', get_config_value('advisor.max_tokens', 500))
        
        raw_response = client.generate_text(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        logger.info("Brief generation successful")
        
        # Format the response
        formatted_brief = format_brief(raw_response)
        
        return formatted_brief
    
    except Exception as e:
        logger.error(f"Failed to generate brief: {str(e)}", exc_info=True)
        
        # Return fallback brief
        return _generate_fallback_brief(anomaly_data)


def generate_batch_briefs(
    anomalies: List[Dict[str, Any]],
    client: Optional[WatsonxClient] = None,
    mode: str = 'individual',
    **kwargs
) -> List[str]:
    """
    Generate operational briefs for multiple anomalies.
    
    Args:
        anomalies: List of anomaly dictionaries
        client: Initialized WatsonxClient (creates new if None)
        mode: Generation mode ('individual' or 'consolidated')
            - individual: Generate separate brief for each anomaly
            - consolidated: Generate single comprehensive brief for all
        **kwargs: Additional parameters
        
    Returns:
        List of operational briefs (one per anomaly if individual, single brief if consolidated)
    """
    logger.info(f"Generating briefs for {len(anomalies)} anomalies in {mode} mode")
    
    # Initialize client if not provided
    if client is None:
        client = initialize_client()
    
    if mode == 'individual':
        # Generate individual briefs
        briefs = []
        for i, anomaly in enumerate(anomalies, 1):
            logger.debug(f"Generating brief {i}/{len(anomalies)}")
            try:
                brief = generate_ops_brief(anomaly, client=client, **kwargs)
                briefs.append(brief)
            except Exception as e:
                logger.error(f"Failed to generate brief {i}: {str(e)}")
                briefs.append(_generate_fallback_brief(anomaly))
        
        logger.info(f"Generated {len(briefs)} individual briefs")
        return briefs
    
    elif mode == 'consolidated':
        # Generate single consolidated brief
        logger.debug("Building consolidated prompt")
        prompt = build_batch_prompt(anomalies, **kwargs)
        
        try:
            temperature = kwargs.get('temperature', get_config_value('advisor.temperature', 0.7))
            max_tokens = kwargs.get('max_tokens', get_config_value('advisor.max_tokens', 1000))
            
            raw_response = client.generate_text(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            formatted_brief = format_brief(raw_response)
            logger.info("Generated consolidated brief")
            
            return [formatted_brief]
        
        except Exception as e:
            logger.error(f"Failed to generate consolidated brief: {str(e)}")
            return [_generate_fallback_batch_brief(anomalies)]
    
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'individual' or 'consolidated'")


def analyze_anomaly_context(anomaly: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and enrich context for anomaly analysis.
    
    This function adds additional contextual information to the anomaly
    data to help generate more informative briefs.
    
    Args:
        anomaly: Anomaly data dictionary
        
    Returns:
        Dictionary with enriched context information
    """
    logger.debug("Analyzing anomaly context")
    
    # Create enriched copy
    enriched = anomaly.copy()
    
    # Add severity classification
    if 'anomaly_score' in anomaly:
        enriched['severity'] = _classify_severity(anomaly['anomaly_score'])
    
    # Add system classification
    sensor_id = anomaly.get('sensor_id', anomaly.get('channel', 'Unknown'))
    enriched['system_type'] = _classify_system(sensor_id)
    
    # Add time-based context
    if 'timestamp' in anomaly:
        enriched['time_context'] = _analyze_temporal_context(anomaly['timestamp'])
    
    # Calculate statistical context
    if 'value' in anomaly and 'mean' in anomaly and 'std' in anomaly:
        enriched['statistical_context'] = _calculate_statistical_context(
            anomaly['value'],
            anomaly['mean'],
            anomaly['std']
        )
    
    logger.debug(f"Context enrichment complete: severity={enriched.get('severity', 'unknown')}")
    
    return enriched


def format_brief(raw_response: str) -> str:
    """
    Structure and format LLM output into standardized brief.
    
    This function cleans up the LLM response and ensures consistent formatting.
    
    Args:
        raw_response: Raw text from LLM
        
    Returns:
        Formatted operational brief
    """
    logger.debug("Formatting brief response")
    
    # Remove leading/trailing whitespace
    formatted = raw_response.strip()
    
    # Remove any prompt artifacts that might have leaked through
    artifacts = [
        "**OPERATIONAL BRIEF:**",
        "**COMPREHENSIVE OPERATIONAL BRIEF:**",
        "Brief:",
        "Assessment:"
    ]
    
    for artifact in artifacts:
        if formatted.startswith(artifact):
            formatted = formatted[len(artifact):].strip()
    
    # Ensure proper paragraph spacing
    formatted = formatted.replace('\n\n\n', '\n\n')
    
    # Add timestamp footer
    from datetime import datetime
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    formatted += f"\n\n---\n*Brief generated: {timestamp}*"
    
    logger.debug(f"Brief formatted, final length: {len(formatted)} characters")
    
    return formatted


def save_brief(
    brief: str,
    output_path: str,
    anomaly_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save operational brief to file.
    
    Args:
        brief: Brief text to save
        output_path: Path to save the brief
        anomaly_id: Optional anomaly identifier
        metadata: Optional metadata to include
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving brief to {output_path}")
    
    # Prepare content
    content = []
    
    # Add header with metadata
    if anomaly_id:
        content.append(f"# Operational Brief - Anomaly {anomaly_id}\n")
    else:
        content.append("# Operational Brief\n")
    
    if metadata:
        content.append("## Metadata\n")
        for key, value in metadata.items():
            content.append(f"- {key}: {value}")
        content.append("\n")
    
    # Add brief content
    content.append("## Brief\n")
    content.append(brief)
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(content))
    
    logger.info(f"Brief saved successfully")


def _classify_severity(anomaly_score: float) -> str:
    """Classify anomaly severity based on score."""
    if anomaly_score >= 0.9:
        return "CRITICAL"
    elif anomaly_score >= 0.75:
        return "HIGH"
    elif anomaly_score >= 0.5:
        return "MEDIUM"
    else:
        return "LOW"


def _classify_system(sensor_id: str) -> str:
    """Classify spacecraft system from sensor ID."""
    sensor_lower = sensor_id.lower()
    
    systems = {
        'thermal': ['temp', 'thermal', 'heat'],
        'power': ['power', 'voltage', 'current', 'battery'],
        'propulsion': ['pressure', 'fuel', 'thrust'],
        'attitude': ['gyro', 'attitude', 'orientation'],
        'communication': ['comm', 'signal', 'antenna']
    }
    
    for system, keywords in systems.items():
        if any(kw in sensor_lower for kw in keywords):
            return system.capitalize()
    
    return "General"


def _analyze_temporal_context(timestamp: Any) -> str:
    """Analyze temporal context of anomaly."""
    # Simple temporal analysis
    # In production, this could check mission phase, orbital position, etc.
    return f"Detected at {timestamp}"


def _calculate_statistical_context(value: float, mean: float, std: float) -> str:
    """Calculate statistical context for the anomaly."""
    if std == 0:
        return "No variation in baseline data"
    
    z_score = abs((value - mean) / std)
    
    if z_score > 3:
        return f"Extreme deviation ({z_score:.1f}σ from mean)"
    elif z_score > 2:
        return f"Significant deviation ({z_score:.1f}σ from mean)"
    else:
        return f"Moderate deviation ({z_score:.1f}σ from mean)"


def _generate_fallback_brief(anomaly: Dict[str, Any]) -> str:
    """Generate a fallback brief when LLM is unavailable."""
    logger.warning("Generating fallback brief (LLM unavailable)")
    
    timestamp = anomaly.get('timestamp', 'Unknown')
    sensor_id = anomaly.get('sensor_id', anomaly.get('channel', 'Unknown'))
    score = anomaly.get('anomaly_score', 0.0)
    value = anomaly.get('value', 'N/A')
    severity = _classify_severity(score)
    
    brief = f"""**OPERATIONAL BRIEF - FALLBACK MODE**

**Anomaly Detected**

An anomaly has been detected in the telemetry data requiring attention.

**Details:**
- Timestamp: {timestamp}
- Sensor/Channel: {sensor_id}
- Measured Value: {value}
- Anomaly Score: {score:.4f}
- Severity: {severity}

**Recommended Actions:**
1. Review detailed telemetry data for the affected sensor
2. Check for correlating anomalies in related systems
3. Verify sensor health and calibration
4. Monitor subsequent telemetry passes for persistence

**Note:** This brief was generated in fallback mode. For detailed analysis, ensure IBM watsonx API is properly configured.
"""
    
    return brief


def _generate_fallback_batch_brief(anomalies: List[Dict[str, Any]]) -> str:
    """Generate a fallback brief for multiple anomalies."""
    logger.warning("Generating fallback batch brief (LLM unavailable)")
    
    total = len(anomalies)
    high_severity = sum(1 for a in anomalies if _classify_severity(a.get('anomaly_score', 0)) in ['CRITICAL', 'HIGH'])
    
    sensors = set(a.get('sensor_id', a.get('channel', 'Unknown')) for a in anomalies)
    
    brief = f"""**OPERATIONAL BRIEF - BATCH ANALYSIS (FALLBACK MODE)**

**Executive Summary**

Multiple anomalies detected in spacecraft telemetry requiring review.

**Summary Statistics:**
- Total Anomalies: {total}
- High/Critical Severity: {high_severity}
- Affected Systems: {len(sensors)}
- Systems: {', '.join(sorted(sensors))}

**Priority Anomalies:**
"""
    
    # Add top 5 anomalies by score
    sorted_anomalies = sorted(anomalies, key=lambda x: x.get('anomaly_score', 0), reverse=True)[:5]
    
    for i, anomaly in enumerate(sorted_anomalies, 1):
        sensor = anomaly.get('sensor_id', anomaly.get('channel', 'Unknown'))
        score = anomaly.get('anomaly_score', 0)
        severity = _classify_severity(score)
        
        brief += f"\n{i}. {sensor} - Score: {score:.4f} ({severity})"
    
    brief += """

**Recommended Actions:**
1. Prioritize investigation of high-severity anomalies
2. Look for patterns or correlations between anomalies
3. Review system logs for the affected time period
4. Schedule detailed analysis with engineering team

**Note:** This brief was generated in fallback mode. For comprehensive analysis, ensure IBM watsonx API is properly configured.
"""
    
    return brief


def create_advisor_pipeline(
    anomalies_df: pd.DataFrame,
    output_dir: Optional[str] = None,
    mode: str = 'individual',
    save_briefs: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Run complete advisor pipeline on detected anomalies.
    
    Args:
        anomalies_df: DataFrame containing detected anomalies
        output_dir: Directory to save briefs (uses config default if None)
        mode: Generation mode ('individual' or 'consolidated')
        save_briefs: Whether to save briefs to disk
        **kwargs: Additional parameters
        
    Returns:
        Dictionary containing briefs and metadata
    """
    logger.info("="*60)
    logger.info("Starting Advisor pipeline")
    logger.info(f"Processing {len(anomalies_df)} anomalies in {mode} mode")
    logger.info("="*60)
    
    # Initialize client
    client = initialize_client()
    
    # Convert DataFrame to list of dictionaries
    anomalies_list = anomalies_df.to_dict('records')
    
    # Generate briefs
    briefs = generate_batch_briefs(
        anomalies_list,
        client=client,
        mode=mode,
        **kwargs
    )
    
    # Save briefs if requested
    if save_briefs:
        if output_dir is None:
            output_dir = get_config_value('paths.briefs_dir', 'data/briefs')
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if mode == 'individual':
            for i, brief in enumerate(briefs):
                output_path = output_dir / f"brief_{timestamp}_{i+1}.md"
                save_brief(brief, str(output_path))
        else:
            output_path = output_dir / f"brief_consolidated_{timestamp}.md"
            save_brief(briefs[0], str(output_path))
        
        logger.info(f"Briefs saved to {output_dir}")
    
    logger.info("="*60)
    logger.info("Advisor pipeline complete")
    logger.info(f"Generated {len(briefs)} brief(s)")
    logger.info("="*60)
    
    return {
        'briefs': briefs,
        'num_anomalies': len(anomalies_df),
        'mode': mode,
        'output_dir': str(output_dir) if save_briefs else None
    }