# 🌾 AgriGuard: AI-Powered Early Plant Disease Triage

![AgriGuard Banner](https://via.placeholder.com/800x200/1e4d1e/ffffff?text=AgriGuard%3A+Smart+Agriculture+Solutions)

## 🎯 Project Overview

AgriGuard is a comprehensive AI-powered platform designed to revolutionize early plant disease detection and agricultural decision-making. Our system combines advanced image validation, disease triage, and smart recommendations to help farmers protect their crops efficiently.

## 🏗️ Project Architecture

```
AgriGuard-Platform/
├── 🖥️  Web Frontend (React + TypeScript + Vite)    [Port 5173]
├── 📱  Mobile App (React Native + Expo)            [Cross-platform]
├── 🔧  Backend API (FastAPI + Python)              [Port 8000]
└── 🧠  AI/ML Models (Image Processing + Validation)
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+ with pip
- Git

### 1. Start Backend Server
```bash
cd redact_aiml_tsec-anurag-dev/backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Web Frontend
```bash
npm install
npm run dev
# Opens on http://localhost:5173
```

### 3. Start Mobile App (Optional)
```bash
cd redact_aiml_tsec-anurag-dev/frontend
npm install
npx expo start
```

## ✨ Features

### 🔍 **Image Validation & Analysis**
- **Format Verification**: Supports JPG, PNG, WebP
- **Corruption Detection**: Advanced file integrity checks
- **Metadata Analysis**: Image dimensions, quality assessment
- **Security Scanning**: Malicious file detection

### 🌱 **Plant Disease Detection**
- **AI-Powered Triage**: Early disease identification
- **Severity Assessment**: Mild, moderate, severe classifications
- **Treatment Recommendations**: Actionable agricultural advice
- **Performance Metrics**: Accuracy tracking and reporting

### 💻 **Multi-Platform Support**
- **Web Application**: Professional desktop interface
- **Mobile App**: iOS/Android with camera integration
- **Cross-Device Sync**: Consistent experience across platforms

### 🎨 **Modern UI/UX**
- **Agricultural Theming**: Green color palette with natural aesthetics
- **Glassmorphism Design**: Modern, translucent interface elements
- **Responsive Layout**: Optimized for all screen sizes
- **Accessibility**: WCAG compliant design standards

## 🛠️ Technology Stack

### Frontend (Web)
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite with HMR
- **Routing**: React Router DOM v7
- **Styling**: Modern CSS with CSS3 animations
- **State Management**: React Hooks

### Frontend (Mobile)
- **Framework**: React Native with Expo
- **Navigation**: Expo Router
- **Camera**: Expo Image Picker
- **Platform**: iOS, Android, Web

### Backend
- **API Framework**: FastAPI
- **Server**: Uvicorn ASGI
- **Image Processing**: Pillow, OpenCV
- **Validation**: Scikit-Image
- **File Handling**: Python-Multipart

### AI/ML
- **Image Analysis**: OpenCV + NumPy
- **Validation**: Scikit-Image algorithms
- **Processing**: PIL/Pillow optimization
- **Detection**: Custom plant disease models

## 📁 Project Structure

```
/src/
├── components/           # Reusable React components
│   ├── Home.tsx         # Landing page with hero section
│   ├── HowItWorks.tsx   # Process explanation
│   ├── Features.tsx     # Feature showcase
│   └── About.tsx        # Team and mission info
├── services/
│   └── api.ts          # Backend API integration
├── assets/             # Images and static files
├── App.tsx            # Main application component
└── App.css           # Global styles and theming

/redact_aiml_tsec-anurag-dev/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI application
│   │   └── validators.py  # Image validation logic
│   ├── temp/             # Temporary file storage
│   └── requirements.txt  # Python dependencies
└── frontend/            # React Native mobile app
    ├── components/
    │   └── ImageUploader.js
    ├── App.js
    └── package.json
```

## 🎮 API Endpoints

### Image Validation
```http
POST /validate-image
Content-Type: multipart/form-data

Response:
{
  "is_valid": true,
  "format": "JPEG",
  "dimensions": [1920, 1080],
  "file_size": 2048576,
  "is_corrupted": false,
  "corruption_details": null
}
```

## 🎨 Design System

### Color Palette
- **Primary Green**: `#1e4d1e` (Dark Forest)
- **Secondary Green**: `#228B22` (Forest Green)
- **Accent Green**: `#32CD32` (Lime Green)
- **Background**: `#f6f9f3` (Light Mint)
- **Text**: `#2c5f2d` (Dark Green)

### Typography
- **Headers**: Bold, agricultural-inspired fonts
- **Body**: Clean, readable sans-serif
- **Accents**: Styled with green highlights

## 🚀 Deployment

### Development
Both frontend and backend run locally with hot-reload for rapid development.

### Production
- **Frontend**: Deploy to Vercel, Netlify, or static hosting
- **Backend**: Deploy to Railway, Render, or cloud platforms
- **Mobile**: Expo EAS Build for app store deployment

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Team

**Built with ❤️ for agricultural innovation**

- Modern web development practices
- AI-powered agricultural solutions
- Sustainable farming technology
- Open-source community collaboration

---

*AgriGuard: Protecting crops, empowering farmers, securing our agricultural future.* 🌾
