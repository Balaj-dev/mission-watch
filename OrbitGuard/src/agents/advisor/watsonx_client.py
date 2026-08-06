"""
IBM watsonx/Granite API client module.

This module handles all interactions with IBM watsonx API for LLM inference.
Supports both real API calls and mock mode for testing without credentials.
"""

from typing import Dict, Any, Optional
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.logger import setup_logger
from src.utils.config_loader import get_config_value

logger = setup_logger(__name__)

# Try to import IBM watsonx SDK
try:
    from ibm_watson_machine_learning.foundation_models import Model
    from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
    WATSONX_AVAILABLE = True
except ImportError:
    logger.warning("IBM watsonx SDK not available. Running in mock mode.")
    WATSONX_AVAILABLE = False


class WatsonxClient:
    """Client for IBM watsonx/Granite API with retry logic and error handling."""
    
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        project_id: str,
        model_name: str = "ibm/granite-13b-instruct-v2",
        mock_mode: bool = False
    ):
        """
        Initialize watsonx API client.
        
        Args:
            api_key: IBM Cloud API key
            endpoint: watsonx API endpoint URL
            project_id: watsonx project ID
            model_name: Model identifier (e.g., 'ibm/granite-13b-instruct-v2')
            mock_mode: If True, use mock responses instead of real API calls
        """
        self.api_key = api_key
        self.endpoint = endpoint
        self.project_id = project_id
        self.model_name = model_name
        self.mock_mode = mock_mode or not WATSONX_AVAILABLE
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.backoff_factor = 2
        
        # Initialize model
        if not self.mock_mode:
            try:
                self._initialize_model()
                logger.info(f"Initialized watsonx client with model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize watsonx client: {str(e)}")
                logger.warning("Falling back to mock mode")
                self.mock_mode = True
        else:
            logger.info("Running in mock mode (no API calls will be made)")
    
    def _initialize_model(self) -> None:
        """Initialize the watsonx foundation model."""
        if not WATSONX_AVAILABLE:
            raise ImportError("IBM watsonx SDK not installed")
        
        # Set up credentials
        credentials = {
            "url": self.endpoint,
            "apikey": self.api_key
        }
        
        # Initialize model
        self.model = Model(
            model_id=self.model_name,
            credentials=credentials,
            project_id=self.project_id
        )
        
        logger.info("watsonx model initialized successfully")
    
    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        top_p: float = 1.0,
        top_k: int = 50,
        repetition_penalty: float = 1.0,
        **kwargs
    ) -> str:
        """
        Generate text using Granite model with retry logic.
        
        Args:
            prompt: Input prompt for the model
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            repetition_penalty: Penalty for repeating tokens
            **kwargs: Additional model parameters
            
        Returns:
            Generated text response
        """
        if self.mock_mode:
            return self._generate_mock_response(prompt)
        
        logger.info(f"Generating text with model: {self.model_name}")
        logger.debug(f"Prompt length: {len(prompt)} characters")
        
        # Prepare generation parameters
        gen_params = {
            GenParams.TEMPERATURE: temperature,
            GenParams.MAX_NEW_TOKENS: max_tokens,
            GenParams.TOP_P: top_p,
            GenParams.TOP_K: top_k,
            GenParams.REPETITION_PENALTY: repetition_penalty
        }
        
        # Add any additional parameters
        gen_params.update(kwargs)
        
        # Attempt generation with retries
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Generation attempt {attempt + 1}/{self.max_retries}")
                
                # Call the model
                response = self.model.generate_text(
                    prompt=prompt,
                    params=gen_params
                )
                
                logger.info("Text generation successful")
                logger.debug(f"Response length: {len(response)} characters")
                
                return response
            
            except Exception as e:
                logger.warning(f"Generation attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    # Calculate delay with exponential backoff
                    delay = self.retry_delay * (self.backoff_factor ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    # Final attempt failed
                    logger.error("All generation attempts failed")
                    self._handle_api_errors(e)
                    raise
    
    def generate_text_batch(
        self,
        prompts: list,
        **kwargs
    ) -> list:
        """
        Generate text for multiple prompts.
        
        Args:
            prompts: List of input prompts
            **kwargs: Generation parameters
            
        Returns:
            List of generated responses
        """
        logger.info(f"Generating text for {len(prompts)} prompts")
        
        responses = []
        for i, prompt in enumerate(prompts, 1):
            logger.debug(f"Processing prompt {i}/{len(prompts)}")
            
            try:
                response = self.generate_text(prompt, **kwargs)
                responses.append(response)
            except Exception as e:
                logger.error(f"Failed to generate text for prompt {i}: {str(e)}")
                responses.append(f"[ERROR: {str(e)}]")
        
        logger.info(f"Batch generation complete: {len(responses)} responses")
        return responses
    
    def _generate_mock_response(self, prompt: str) -> str:
        """
        Generate a mock response for testing without API access.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Mock response text
        """
        logger.debug("Generating mock response")
        
        # Analyze prompt to generate contextual mock response
        if "anomaly" in prompt.lower() or "anomalies" in prompt.lower():
            return self._generate_mock_anomaly_brief()
        elif "summary" in prompt.lower():
            return self._generate_mock_summary()
        else:
            return self._generate_generic_mock_response()
    
    def _generate_mock_anomaly_brief(self) -> str:
        """Generate a mock operational brief for anomalies."""
        return """**OPERATIONAL BRIEF - TELEMETRY ANOMALY DETECTION**

**Executive Summary:**
Multiple anomalies detected in spacecraft telemetry data requiring immediate attention. Analysis indicates potential issues with thermal control and power systems.

**Key Findings:**
1. **Thermal Anomalies (High Priority)**
   - Temperature sensor readings exceeded normal operating range by 15%
   - Detected in channels: thermal_sensor_1, thermal_sensor_2
   - Time window: 2024-01-15 14:30:00 to 14:45:00 UTC
   - Recommendation: Verify thermal control system operation

2. **Power System Irregularities (Medium Priority)**
   - Voltage fluctuations observed in power_bus_voltage
   - Anomaly score: 0.85 (high confidence)
   - Possible causes: Battery degradation or solar panel efficiency loss
   - Recommendation: Schedule power system diagnostic

3. **Communication Link Quality (Low Priority)**
   - Signal strength variations within acceptable limits
   - No immediate action required, continue monitoring

**Recommended Actions:**
- Immediate: Review thermal control system logs
- Short-term: Schedule power system health check
- Long-term: Implement enhanced monitoring for identified channels

**Confidence Level:** High (based on Isolation Forest model with 0.05 contamination)

**Next Review:** Scheduled for next telemetry pass in 4 hours
"""
    
    def _generate_mock_summary(self) -> str:
        """Generate a mock summary response."""
        return """**Summary:**
The telemetry data analysis has been completed successfully. Key metrics are within normal operating parameters with a few exceptions noted for further investigation. Overall system health appears nominal with minor anomalies detected in thermal and power subsystems.
"""
    
    def _generate_generic_mock_response(self) -> str:
        """Generate a generic mock response."""
        return """Based on the provided information, I have analyzed the data and generated this response. This is a mock response for testing purposes when the IBM watsonx API is not available. In production, this would be replaced with actual LLM-generated content from the Granite model.
"""
    
    def _handle_api_errors(self, error: Exception) -> None:
        """
        Handle API errors with detailed logging.
        
        Args:
            error: Exception from API call
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        logger.error(f"API Error ({error_type}): {error_msg}")
        
        # Log specific error types
        if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            logger.error("Authentication failed. Check API key and credentials.")
        elif "rate limit" in error_msg.lower():
            logger.error("Rate limit exceeded. Consider implementing request throttling.")
        elif "timeout" in error_msg.lower():
            logger.error("Request timeout. Check network connectivity and endpoint availability.")
        elif "quota" in error_msg.lower():
            logger.error("API quota exceeded. Check usage limits.")
        else:
            logger.error("Unexpected API error. Check logs for details.")
    
    def test_connection(self) -> bool:
        """
        Test the connection to watsonx API.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.mock_mode:
            logger.info("Mock mode enabled - connection test skipped")
            return True
        
        logger.info("Testing watsonx API connection")
        
        try:
            # Try a simple generation
            test_prompt = "Hello, this is a connection test."
            response = self.generate_text(
                test_prompt,
                max_tokens=10,
                temperature=0.1
            )
            
            if response:
                logger.info("Connection test successful")
                return True
            else:
                logger.error("Connection test failed: Empty response")
                return False
        
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'endpoint': self.endpoint,
            'project_id': self.project_id,
            'mock_mode': self.mock_mode,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'watsonx_sdk_available': WATSONX_AVAILABLE
        }


def initialize_client(
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    project_id: Optional[str] = None,
    model_name: Optional[str] = None,
    mock_mode: Optional[bool] = None
) -> WatsonxClient:
    """
    Factory function to create and initialize watsonx client.
    
    Loads configuration from config.yaml if parameters not provided.
    
    Args:
        api_key: IBM Cloud API key (loads from config if None)
        endpoint: watsonx API endpoint URL (loads from config if None)
        project_id: watsonx project ID (loads from config if None)
        model_name: Model identifier (loads from config if None)
        mock_mode: Force mock mode (auto-detects if None)
        
    Returns:
        Initialized WatsonxClient instance
    """
    logger.info("Initializing watsonx client")
    
    # Load from config if not provided
    if api_key is None:
        api_key = get_config_value('advisor.watsonx.api_key', '')
    
    if endpoint is None:
        endpoint = get_config_value('advisor.watsonx.endpoint', 'https://us-south.ml.cloud.ibm.com')
    
    if project_id is None:
        project_id = get_config_value('advisor.watsonx.project_id', '')
    
    if model_name is None:
        model_name = get_config_value('advisor.watsonx.model_name', 'ibm/granite-13b-instruct-v2')
    
    # Determine mock mode
    if mock_mode is None:
        # Auto-detect: use mock if no API key or SDK not available
        mock_mode = not api_key or not WATSONX_AVAILABLE
    
    if mock_mode:
        logger.warning("Initializing in mock mode - no real API calls will be made")
    
    # Create client
    client = WatsonxClient(
        api_key=api_key,
        endpoint=endpoint,
        project_id=project_id,
        model_name=model_name,
        mock_mode=mock_mode
    )
    
    logger.info("watsonx client initialization complete")
    
    return client