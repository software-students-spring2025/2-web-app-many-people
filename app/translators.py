import os
import json
from openai import OpenAI

# Language codes and names
LANGUAGES = {
    'zh': 'Chinese',
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
}

# Chinese translation instructions
CHINESE_INSTRUCTIONS = """
IMPORTANT INSTRUCTION FOR CHINESE TRANSLATIONS:
1. DO NOT include pinyin or phonetic pronunciations ANYWHERE in the response.
2. Leave the phonetic field empty.
3. Do not include romanization in brackets like (wèi lái) after Chinese characters.
4. All examples should use only Chinese characters without pinyin.
5. Do not add pronunciation guides in any field.
"""





class OpenAITranslator:
    """Translator implementation using Gemini API"""
    
    def __init__(self):
        # Initialize with Gemini API key from environment
        self.api_key = os.environ.get('GEMINI_API_KEY', None)
        # Use the OpenAI-compatible endpoint
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        self.model = "gemini-2.0-flash"
        
        if not self.api_key:
            print("WARNING: Gemini API key not found. Using mock translation.")
        else:
            # Initialize OpenAI client with Gemini API compatible endpoint
            try:
                print("Attempting to initialize OpenAI client...")
                print(f"API Key available: {'Yes' if self.api_key else 'No'}")
                print(f"Base URL: {self.base_url}")
                
                # Use only the essential parameters for OpenAI client
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                
                print("OpenAI client initialized successfully")
            except Exception as e:
                print(f"Error initializing OpenAI client: {e}")
                self.client = None

    def _create_system_prompt(self, prompt_type, source_lang_name, target_lang_name, target_language, user_focus, focus_instruction):
        """Create a system prompt based on the prompt type and parameters"""
        if prompt_type == "dictionary":
            return f"""You are a comprehensive {target_lang_name} dictionary. {focus_instruction}
                    Please provide detailed information about the word in a structured JSON format.

                    Analyze the word and provide detailed information in {target_lang_name}.
                    If this word has a SPECIFIC MEANING in the context of '{user_focus}' (if applicable), create a separate translation entry with "is_specialized_term": true and "topic": "{user_focus}".

                    {CHINESE_INSTRUCTIONS if target_language == 'zh' else ""}

                    For each entry, follow this EXACT structure in valid JSON format:
                    {{
                    "translations": [
                        {{
                        "word": "the original word",
                        "phonetic": "{'' if target_language == 'zh' else 'pronunciation in IPA format'}",
                        "partOfSpeech": "part of speech (noun, verb, adjective, etc.)",
                        "meaning": "definition in {target_lang_name}",
                        "context": "how and when the word is used",
                        "is_specialized_term": false,
                        "topic": "",
                        "wordForms": {{
                            "pluralForm": "",
                            "pastTense": "",
                            "presentParticiple": "",
                            "comparativeForm": "",
                            "superlativeForm": ""
                        }},
                        "synonyms": ["synonym1", "synonym2"],
                        "examples": [
                            {{ "original": "Example sentence", "translated": "Translation of the example" }}
                        ]
                        }}
                    ]
                    }}

                    Your response MUST be only valid JSON, with no explanations before or after."""
        
        elif prompt_type == "translation":
            return f"""You are a professional {source_lang_name} to {target_lang_name} translator. {focus_instruction}
                        Translate the text and provide detailed information in a structured JSON format.

                        If the text contains terms with SPECIFIC MEANINGS in the context of '{user_focus}' (if applicable), highlight those with "is_specialized_term": true and "topic": "{user_focus}".

                        {CHINESE_INSTRUCTIONS if target_language == 'zh' else ""}

                        For each translation, follow this EXACT structure in valid JSON format:
                        {{
                        "translations": [
                            {{
                            "word": "the original word/term",
                            "phonetic": "{'' if target_language == 'zh' else f'pronunciation in {target_lang_name}'}",
                            "partOfSpeech": "part of speech (noun, verb, adjective, etc.)",
                            "meaning": "translation in {target_lang_name}",
                            "context": "how and when the term is used",
                            "is_specialized_term": false,
                            "topic": "",
                            "wordForms": {{
                                "pluralForm": "",
                                "pastTense": "",
                                "presentParticiple": "",
                                "comparativeForm": "",
                                "superlativeForm": ""
                            }},
                            "synonyms": ["synonym1", "synonym2"],
                            "examples": [
                                {{ "original": "Example using the term", "translated": "Translation of the example" }}
                            ]
                            }}
                        ]
                        }}
                        Your response MUST be only valid JSON, with no explanations before or after."""
                                
        elif prompt_type == "simple":
            return f"""You are a professional {source_lang_name} to {target_lang_name} translator.
                        Translate the text accurately, preserving the meaning and tone of the original.
                        Provide ONLY the translation, with no additional explanations or context."""                   
        else:
            return ""

    def translate(self, text, target_language, source_language='auto', provide_details=False, user_focus=None):
        """
        Translate text using the LLM
        """
        # If no API key is set, use mock translation
        if not self.api_key:
            print("No API key available, using mock translation")
            return self._mock_translate(text, target_language, source_language, provide_details, user_focus)
        
        try:
            # Get the full language name for better context
            target_lang_name = LANGUAGES.get(target_language, target_language)
            source_lang_name = LANGUAGES.get(source_language, source_language) if source_language != 'auto' else 'any language'
            
            # Handle case when source and target languages are the same
            if source_language != 'auto' and source_language == target_language:
                # When source and target language are the same, we treat this as a dictionary lookup
                if provide_details:
                    focus_instruction = ""
                    if user_focus and user_focus.strip():
                        focus_instruction = f"Focus particularly on contexts related to {user_focus}."
                    
                    system_prompt = self._create_system_prompt("dictionary", source_lang_name, target_lang_name, target_language, user_focus, focus_instruction)
                    user_message = f"Word to provide details for: {text}"
                    
                    # Use the helper function for API call - only use mock_translate on exception
                    result_text = self._call_api(
                        system_prompt, 
                        user_message, 
                        json_response=True
                    )
                    
                    if result_text:
                        return self._process_api_response(result_text, target_language, source_language, text)
                
                # For same-language lookups with no details, use a simpler API call 
                system_prompt = self._create_system_prompt("simple", source_lang_name, target_lang_name, target_language, None, "")
                user_message = f"Provide a definition for the {source_lang_name} word: {text}"
                
                # Make a simpler API call for dictionary lookup
                translation = self._call_api(
                    system_prompt, 
                    user_message
                )
                
                if translation:
                    return {
                        'translation': translation.strip(),
                        'source_language': source_language,
                        'target_language': target_language,
                        'query': text
                    }
            
            # For cross-language translations
            else:
                # Set up translation parameters
                if provide_details:
                    focus_instruction = ""
                    if user_focus and user_focus.strip():
                        focus_instruction = f"Focus particularly on contexts related to {user_focus}."
                    
                    system_prompt = self._create_system_prompt("translation", source_lang_name, target_lang_name, target_language, user_focus, focus_instruction)
                    user_message = f"Text to translate from {source_lang_name} to {target_lang_name}: {text}"
                    
                    # Use the helper function for API call - only use mock_translate on exception
                    result_text = self._call_api(
                        system_prompt, 
                        user_message, 
                        json_response=True
                    )
                    
                    if result_text:
                        return self._process_api_response(result_text, target_language, source_language, text)
                else:
                    # For simple translations without details
                    system_prompt = self._create_system_prompt("simple", source_lang_name, target_lang_name, target_language, None, "")
                    user_message = f"Translate from {source_lang_name} to {target_lang_name}: {text}"
                    
                    # Use the helper function for API call
                    translation = self._call_api(
                        system_prompt, 
                        user_message
                    )
                    
                    # If we got a result from the API
                    if translation:
                        return {
                            'translation': translation.strip(),
                            'source_language': source_language,
                            'target_language': target_language,
                            'query': text
                        }
            
            # If execution reaches here, API calls failed without exceptions
            # Use mock translate as last resort
            return self._mock_translate(text, target_language, source_language, provide_details, user_focus)
                        
        except Exception as e:
            print(f"Error in translate method: {e}")
            # Fall back to mock translation only on exception
            return self._mock_translate(text, target_language, source_language, provide_details, user_focus)
    
    def _format_translations(self, translation_data):
        """Format structured translation data into readable text"""
        if not translation_data or 'translations' not in translation_data:
            return "No translation data available."
            
        translations = translation_data['translations']
        if not translations:
            return "No translations found."
            
        formatted_text = ""
        
        for i, trans in enumerate(translations):
            # Add translation header with word and part of speech
            word = trans.get('word', 'Unknown')
            pos = trans.get('partOfSpeech', '')
            phonetic = trans.get('phonetic', '')
            
            # Add separator between multiple translations
            if i > 0:
                formatted_text += "\n\n" + "=" * 40 + "\n"
                
            # Add title with basic information
            formatted_text += f"\n{word}"
            if pos:
                formatted_text += f" [{pos}]"
            if phonetic:
                formatted_text += f" {phonetic}"
                
            # Add specialized term indicator and topic if applicable
            is_specialized = trans.get('is_specialized_term', False)
            topic = trans.get('topic', '')
            if is_specialized and topic:
                formatted_text += f"\n[Specialized term in {topic}]"
                
            # Add meaning and context
            meaning = trans.get('meaning', '')
            context = trans.get('context', '')
            if meaning:
                formatted_text += f"\n\nMeaning: {meaning}"
            if context:
                formatted_text += f"\nContext: {context}"
                
            # Add word forms if available
            word_forms = trans.get('wordForms', {})
            if word_forms and any(value for key, value in word_forms.items() if value):
                formatted_text += "\n\nWord Forms:"
                for form_name, form_value in word_forms.items():
                    if form_value:
                        # Convert camelCase to Title Case with spaces
                        form_display = ''.join(' ' + c if c.isupper() else c for c in form_name).strip().title()
                        formatted_text += f"\n  {form_display}: {form_value}"
                        
            # Add synonyms if available
            synonyms = trans.get('synonyms', [])
            if synonyms:
                formatted_text += f"\n\nSynonyms: {', '.join(synonyms)}"
                
            # Add examples if available
            examples = trans.get('examples', [])
            if examples:
                formatted_text += "\n\nExamples:"
                for ex in examples:
                    original = ex.get('original', '')
                    translated = ex.get('translated', '')
                    if original:
                        formatted_text += f"\n  • {original}"
                        if translated:
                            formatted_text += f"\n    {translated}"
        
        return formatted_text
        
    def _mock_translate(self, text, target_language, source_language='auto', provide_details=False, user_focus=None):
        """Generate mock translation data for testing or when API is unavailable"""
        # Create a mock translation response
        if provide_details:
            # Mock detailed response for dictionary lookup
            is_specialized = user_focus and any(term in text.lower() for term in ['trade', 'money', 'market', 'stock', 'finance', 'economy'])
            
            # For Chinese translations, don't include phonetic pronunciation
            phonetic_value = "" if target_language == 'zh' else "/mɒk prəˌnʌnsɪˈeɪʃn/"
            
            mock_response = {
                "translations": [
                    {
                        "word": text,
                        "phonetic": phonetic_value,
                        "partOfSpeech": "noun",
                        "meaning": f"Mock translation of '{text}' to {target_language}",
                        "context": "General usage context",
                        "is_specialized_term": False,
                        "topic": "",
                        "wordForms": {
                            "pluralForm": f"{text}s",
                            "pastTense": "",
                            "presentParticiple": "",
                            "comparativeForm": "",
                            "superlativeForm": ""
                        },
                        "synonyms": ["similar1", "similar2"],
                        "examples": [
                            {
                                "original": f"This is an example using {text}.",
                                "translated": f"Mock translation of the example."
                            }
                        ]
                    }
                ]
            }
            
            # Add specialized term if relevant
            if is_specialized:
                specialized_entry = {
                    "word": text,
                    "phonetic": phonetic_value,
                    "partOfSpeech": "noun",
                    "meaning": f"Specialized {user_focus} meaning of '{text}'",
                    "context": f"Used in {user_focus} contexts",
                    "is_specialized_term": True,
                    "topic": user_focus,
                    "wordForms": {
                        "pluralForm": f"{text}s",
                        "pastTense": "",
                        "presentParticiple": "",
                        "comparativeForm": "",
                        "superlativeForm": ""
                    },
                    "synonyms": [f"{user_focus} term1", f"{user_focus} term2"],
                    "examples": [
                        {
                            "original": f"This is a {user_focus} example using {text}.",
                            "translated": f"Mock translation of the {user_focus} example."
                        }
                    ]
                }
                mock_response["translations"].append(specialized_entry)
            
            
            return {
                'translation_data': mock_response,
                'formatted_text': self._format_translations(mock_response),
                'source_language': source_language,
                'target_language': target_language,
                'query': text
            }
        else:
            # Simple translation
            return {
                'translation': f"Mock translation of '{text}' to {target_language}",
                'source_language': source_language,
                'target_language': target_language,
                'query': text
            }

    def _process_api_response(self, result_text, target_language, source_language, text):
        """Process API response and apply post-processing"""
        try:
            # Parse the JSON response
            parsed_response = json.loads(result_text)
            
            # Return formatted result with all needed data
            return {
                'translation_data': parsed_response,
                'formatted_text': self._format_translations(parsed_response),
                'source_language': source_language,
                'target_language': target_language,
                'query': text
            }
        except Exception as e:
            print(f"Error processing API response: {e}")
            return self._mock_translate(text, target_language, source_language, True, None)

    def _call_api(self, system_prompt, user_message, json_response=False):
        """
        Helper function to make API calls with consistent error handling
        
        Args:
            system_prompt: The system prompt to use
            user_message: The user message to send
            json_response: Whether to expect a JSON response
            
        Returns:
            The API response text or None if the call fails
        """
        if not self.api_key or not self.client:
            return None
            
        try:
            # Prepare API call parameters
            params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            }
            
            # Add response format if JSON is expected
            if json_response:
                params["response_format"] = {"type": "json_object"}
                
            # Make the API call
            completion = self.client.chat.completions.create(**params)
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"API call error: {e}")
            return None


# Instantiate the translator
translator = OpenAITranslator() 