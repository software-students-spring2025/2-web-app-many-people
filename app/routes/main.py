import re
import datetime
from bson.objectid import ObjectId
from functools import wraps
from flask import Blueprint, request, render_template, redirect, url_for, session, flash, current_app, jsonify

# Import the models and translator from translators module
from app.translators import translator

main = Blueprint('main', __name__)

# Language codes and names
LANGUAGES = {
    'zh': 'Chinese',
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
}

# Decorator for requiring login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login'))
        
        # Set current user info for the request
        current_user.id = session.get('user_id')
        current_user.is_authenticated = True
        
        return f(*args, **kwargs)
    return decorated_function

# Simple mock for current_user when no auth system is implemented
class current_user:
    id = None
    is_authenticated = False
    topic = None

def translate_text(text, target_language, source_language='auto', provide_details=False, user_focus=None):
    """Translate text using the translator from the translators module"""
    return translator.translate(text, target_language, source_language, provide_details, user_focus)


def format_translations(translation_data):
    """Format structured translation data into readable text"""
    return translator._format_translations(translation_data)

@main.route('/')
def index():
    return redirect(url_for('auth.login'))

@main.route('/lookup', methods=['GET', 'POST'])
@login_required
def lookup():
    # Get available languages
    languages = LANGUAGES
    result = None
    
    # Set default language to Chinese
    current_language = request.args.get('lang', 'zh')
    
    # Get user's topic preference (either from request or from user profile)
    current_topic = request.args.get('topic', None)
    if not current_topic and hasattr(current_user, 'topic'):
        current_topic = current_user.topic
    
    if request.method == 'POST':
        word = request.form.get('word', '').strip()
        target_language = request.form.get('target_language')
        
        # Get topic from the form if available
        user_focus = request.form.get('topic', current_topic)
        
        if word and target_language:
            # Attempt to detect source language of the input text if possible
            # For short words/phrases, this might not be very accurate
            detected_source = 'auto'
            
            # If the word contains Chinese characters, set source to Chinese
            if any('\u4e00' <= char <= '\u9fff' for char in word):
                detected_source = 'zh'
            # If the word contains only Latin alphabet and common punctuation, try to set it to English/French/Spanish/etc.
            elif all(ord(c) < 128 for c in word):
                # Simple heuristic: Check if it matches English words pattern
                # This is not perfect but provides a basic guess
                if re.match(r'^[a-zA-Z]+$', word):
                    detected_source = 'en'  # Default to English for Latin alphabet words
            
            # Call the translation function with detailed information
            result = translate_text(
                word, 
                target_language, 
                source_language=detected_source, 
                provide_details=True,
                user_focus=user_focus
            )
            
            # Pass source_language to the template for handling examples display
            result['source_language'] = detected_source
            
            # Extract the main translation from result
            main_translation = ""
            if 'translation' in result:
                main_translation = result['translation']
            elif 'formatted_text' in result:
                main_translation = result['formatted_text']
            elif 'translation_data' in result and result['translation_data']:
                if 'translations' in result['translation_data']:
                    translations = result['translation_data']['translations']
                    if translations and len(translations) > 0:
                        main_translation = translations[0].get('meaning', '')
            
            # Fallback extraction if no translation found
            if not main_translation and isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, str) and value and key not in ['source_language', 'target_language', 'query']:
                        main_translation = value
                        break
            
            # Save to history
            if current_app.db is not None:
                try:
                    lookup_history = {
                        'user_id': ObjectId(current_user.id),
                        'word': word,
                        'result': {
                            'translation': main_translation,
                            'details': result.get('details', {}),
                            'source_language': result.get('source_language', 'auto'),
                            'target_language': target_language
                        },
                        'target_language': target_language,
                        'created_at': datetime.datetime.now(),
                        'type': 'lookup'
                    }
                    
                    current_app.db.history.insert_one(lookup_history)
                    
                except Exception as e:
                    print(f"Error saving lookup history: {str(e)}")
                
            return render_template(
                'lookup.html', 
                result=result, 
                languages=languages, 
                current_language=target_language,
                current_topic=user_focus
            )
    
    return render_template(
        'lookup.html', 
        languages=languages, 
        current_language=current_language,
        current_topic=current_topic,
        result=result
    )

@main.route('/translate', methods=['GET', 'POST'])
@login_required
def translate():
    languages = LANGUAGES
    result = None
    
    # Set default language
    target_language = request.args.get('lang', 'zh')
    
    # Get user's topic preference (either from request or from user profile)
    current_topic = request.args.get('topic', None)
    if not current_topic and hasattr(current_user, 'topic'):
        current_topic = current_user.topic
    
    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        target_language = request.form.get('target_language', target_language)  # Use request form value or fallback to the one from args
        
        # Get topic from the form if available
        user_focus = request.form.get('topic', current_topic)
        
        if text:
            # Get translation without details, but with user's focus
            translation_result = translate_text(text, target_language, provide_details=False, user_focus=user_focus)
            
            # Create a simplified result structure for the translate page
            if translation_result:
                # Extract the translation from the result
                main_translation = ""
                if isinstance(translation_result, dict):
                    main_translation = translation_result.get('translation', '')
                else:
                    main_translation = str(translation_result)
                
                result = {
                    'translation': main_translation,
                    'source_language': translation_result.get('source_language', 'auto') if isinstance(translation_result, dict) else 'auto',
                    'target_language': translation_result.get('target_language', target_language) if isinstance(translation_result, dict) else target_language,
                    'query': text
                }
                
                # Save to history
                if current_app.db is not None:
                    try:
                        translation_history = {
                            'user_id': ObjectId(current_user.id),
                            'text': text,
                            'result': {
                                'translation': main_translation
                            },
                            'target_language': target_language,
                            'created_at': datetime.datetime.now(),
                            'type': 'translate'
                        }
                        
                        current_app.db.history.insert_one(translation_history)
                    except Exception as e:
                        print(f"Error saving translation history: {str(e)}")
    
    return render_template('translate.html', 
                          result=result, 
                          languages=languages, 
                          current_language=target_language,
                          current_topic=current_topic)

@main.route('/mylist')
@login_required
def mylist():
    saved_items = []
    
    if current_app.db is not None:
        saved_items = list(current_app.db.saved_translations.find(
            {'user_id': ObjectId(current_user.id)}
        ).sort('created_at', -1))
    
    return render_template('mylist.html', saved_items=saved_items, languages=LANGUAGES)

@main.route('/save_translation', methods=['POST'])
@login_required
def save_translation():
    if request.method == 'POST':
        text = request.form.get('text')
        translation = request.form.get('translation')
        target_language = request.form.get('target_language')
        translation_type = request.form.get('type', 'lookup')  # lookup or translate
        topic = request.form.get('topic', '')
        
        try:
            if text and translation and current_app.db is not None:
                saved_item = {
                    'user_id': ObjectId(current_user.id),
                    'text': text,
                    'translation': translation,
                    'target_language': target_language,
                    'created_at': datetime.datetime.now(),
                    'note': '',
                    'type': translation_type,
                    'topic': topic
                }
                current_app.db.saved_translations.insert_one(saved_item)
                flash('Translation saved successfully!')
                
                # Redirect back to the appropriate page
                if translation_type == 'lookup':
                    return redirect(url_for('main.lookup'))
                else:
                    return redirect(url_for('main.translate'))
            else:
                if not text or not translation:
                    flash('Error: Missing text or translation')
                elif not current_app.db:
                    flash('Error: Database connection not available')
        except Exception as e:
            flash(f'Error saving translation: {str(e)}')
    
    # Default return if no conditions are met or if there's an error
    return redirect(url_for('main.index'))

@main.route('/delete_saved/<item_id>', methods=['POST'])
@login_required
def delete_saved(item_id):
    if current_app.db is not None:
        current_app.db.saved_translations.delete_one({
            '_id': ObjectId(item_id),
            'user_id': ObjectId(current_user.id)
        })
        flash('Item removed from your list')
    
    return redirect(url_for('main.mylist'))

@main.route('/edit_note/<item_id>', methods=['POST'])
@login_required
def edit_note(item_id):
    if request.method == 'POST' and current_app.db is not None:
        note = request.form.get('note', '')
        
        current_app.db.saved_translations.update_one(
            {'_id': ObjectId(item_id), 'user_id': ObjectId(current_user.id)},
            {'$set': {'notes': note}}
        )
        flash('Note updated')
    
    return redirect(url_for('main.mylist'))

@main.route('/search_history', methods=['GET'])
@login_required
def search_history():
    query = request.args.get('q', '').strip()
    history_items = []
    
    if query and current_app.db is not None:
        # Search across all relevant fields
        history_items = list(current_app.db.history.find({
            'user_id': ObjectId(current_user.id),
            '$or': [
                {'word': {'$regex': query, '$options': 'i'}},
                {'text': {'$regex': query, '$options': 'i'}},
                {'result.translation': {'$regex': query, '$options': 'i'}}
            ]
        }).sort('created_at', -1))
    
    return render_template('search_results.html', 
                          history_items=history_items, 
                          query=query, 
                          languages=LANGUAGES)

@main.route('/api/translate', methods=['POST'])
def api_translate():
    data = request.get_json()
    text = data.get('text', '')
    target_language = data.get('target_language', 'en')
    source_language = data.get('source_language', 'auto')
    provide_details = data.get('provide_details', False)
    user_focus = data.get('user_focus', None)
    
    if not text.strip():
        return jsonify({'error': 'Text is required'}), 400
    
    result = translate_text(text, target_language, source_language, provide_details, user_focus)
    
    return jsonify(result)

@main.route('/api/lookup', methods=['POST'])
def api_lookup():
    data = request.get_json()
    word = data.get('word', '')
    language = data.get('language', 'en')
    user_focus = data.get('user_focus', None)
    
    if not word.strip():
        return jsonify({'error': 'Word is required'}), 400
    
    result = translate_text(word, language, language, True, user_focus)
    
    return jsonify(result) 