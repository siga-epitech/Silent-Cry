require('dotenv').config();
const express = require('express');
const axios = require('axios');
const app = express();

// Middleware
app.use(express.json());

// Configuration
const AUTH_SERVICE_URL = process.env.AUTH_SERVICE_URL || 'http://auth-service:9000';
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://ai-service:5000';


// Proxy vers Auth Service
app.post('/login', async (req, res) => {
  try {
    const response = await axios.post(`${AUTH_SERVICE_URL}/login`, req.body);
    res.json(response.data);
  } catch (err) {
    res.status(err.response?.status || 500).json({
      error: 'Authentication failed',
      details: err.response?.data || err.message
    });
  }
});

// Route protégée
app.post('/analyze', async (req, res) => {
  try {
    // Vérification du token via Auth Service
    const authHeader = req.headers['authorization'];
    const token = authHeader?.split(' ')[1];
    
    if (!token) return res.sendStatus(401);
    
    // Validation du token
    const authCheck = await axios.get(`${AUTH_SERVICE_URL}/validate`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    
    if (authCheck.status !== 200) return res.sendStatus(403);

    // Appel à l'AI Service
    const result = await axios.post(`${AI_SERVICE_URL}/analyze`, req.body, {
      headers: { Authorization: `Bearer ${token}` }
    });
    
    res.json(result.data);
  } catch (err) {
    console.error('Analyze error:', err);
    res.status(err.response?.status || 500).json({
      error: "Erreur d'analyse",
      details: err.response?.data || err.message
    });
  }
});

// Documentation
app.get('/', (req, res) => {
  res.json({
    message: 'Silent Cry API Gateway',
    endpoints: {
      status: 'GET /api/status',
      login: 'POST /login',
      analyze: 'POST /analyze'
    },
    _links: {
      auth_service: AUTH_SERVICE_URL,
      ai_service: AI_SERVICE_URL
    }
  });
});

// Health Check
app.get('/api/status', (req, res) => {
  res.json({
    status: 'API Gateway operational',
    services: {
      auth: AUTH_SERVICE_URL,
      ai: AI_SERVICE_URL,
      db: 'PostgreSQL'
    },
    timestamp: new Date()
  });
});

// Démarrer le serveur
app.listen(8000, () => {
  console.log(`API Gateway running on http://localhost:8000`);
  console.log(`Auth Service: ${AUTH_SERVICE_URL}`);
  console.log(`AI Service: ${AI_SERVICE_URL}`);
});