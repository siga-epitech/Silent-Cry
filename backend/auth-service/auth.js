require('dotenv').config();
const jwt = require('jsonwebtoken');
const express = require('express');
const app = express();

app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).send('OK');
});

app.post('/login', (req, res) => {
  const token = jwt.sign({ user: 'parent' }, process.env.JWT_SECRET, { expiresIn: '1h' });
  res.send({ token });
});

// Route de validation
app.get('/validate', (req, res) => {
  const token = req.headers['authorization']?.split(' ')[1];
  if (!token) return res.sendStatus(401);

  jwt.verify(token, process.env.JWT_SECRET, (err) => {
    if (err) return res.sendStatus(403);
    res.sendStatus(200);
  });
});

app.listen(9000, () => console.log('Auth running on 9000'));