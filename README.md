# TranslateGo

## Product vision statement

An AI powered translation application that helps users quickly look up words, accurately translate text between multiple languages, save translations for future reference, and customize their experience based on specialized topics of interest.

## User stories

- As an ELL student, I want to translate unfamiliar English words I encounter in my textbooks so that I can understand my assignments without constantly interrupting my reading flow.
- As an ELL student, I want to see side-by-side translations of English texts with my native language so that I can compare sentence structures and improve my understanding of English grammar.
- As an ELL student, I want to see multiple possible translations for English words I look up so that I can select the one that best fits my context.
- As a content creator, I want to translate longer texts while maintaining the original tone and style so that my work resonates with audiences in different languages.
- As a traveler, I want to quickly look up foreign words I encounter on signs or menus so that I can understand my surroundings in a new country without carrying a physical dictionary.
- As a researcher, I want to customize the translation engine to recognize specialized scientific terminology so that I receive accurate translations in my field of expertise.

## Steps necessary to run the software

### Method 1: Standard Setup

1. **Prerequisites**
   - Python 3.8 or higher
   - MongoDB (local installation or MongoDB Atlas account)
   - OpenAI API key and Google Gemini API key
   - Git

2. **Clone the repository**
   ```bash
   git clone https://github.com/software-students-spring2025/2-web-app-many-people
   cd 2-web-app-many-people
   ```

3. **Set up a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   - Create a `.env` file in the project root
   - Add the following variables (see `env.example` for reference):
     ```
     FLASK_APP=app
     FLASK_ENV=development
     FLASK_DEBUG=1
     FLASK_PORT=5001
     
     # MongoDB Configuration
     MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/dbname
     MONGO_DBNAME=your_database_name
     
     # Flask Secret Key
     SECRET_KEY=your_secret_key_here
     
     # API Keys for Translation Services
     GEMINI_API_KEY=your_gemini_api_key_here
     ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Access the application**
   - Open your browser and navigate to `http://localhost:5001`

### Method 2: Docker Setup (Recommended)

1. **Prerequisites**
   - Docker and Docker Compose
   - Git
   - Google Gemini API key

2. **Clone the repository**
   ```zsh
   git clone https://github.com/software-students-spring2025/2-web-app-many-people
   cd 2-web-app-many-people
   ```

3. **Configure environment variables**
   - Create a `.env` file in the project root
   - Add the following API keys:
     ```
     # Flask Secret Key
     SECRET_KEY=your_secret_key_here
     
     # API Keys for Translation Services
     GEMINI_API_KEY=your_gemini_api_key_here
     ```

4. **Build and start the Docker containers**
   ```zsh
   docker-compose up -d
   ```

5. **Access the application**
   - Open your browser and navigate to `http://localhost:5001`
   - The application is now running with a MongoDB database in Docker containers

6. **Stop the containers when done**
   ```zsh
   docker-compose down
   ```

## Task boards



## Contributors
- [Alan Chen](https://github.com/Chen-zexi)
