import express from 'express';
import { createServer as createViteServer } from 'vite';
import { GoogleGenAI } from '@google/genai';

async function startServer() {
  const app = express();
  app.use(express.json());

  const ai = new GoogleGenAI({
    apiKey: process.env.GEMINI_API_KEY || '',
    httpOptions: {
      headers: {
        'User-Agent': 'aistudio-build',
      },
    },
  });

  // Chat API endpoint
  app.post('/api/chat', async (req, res) => {
    try {
      const { messages, system } = req.body;

      const contents = (messages || []).map((m: any) => ({
        role: m.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: String(m.content || '') }],
      }));

      const config: any = {};
      if (system) {
        config.systemInstruction = system;
      }

      const candidateModels = ['gemini-3.1-flash-lite', 'gemini-3.8-flash', 'gemini-flash-latest'];
      let responseText = '';
      let lastError: any = null;

      for (const m of candidateModels) {
        try {
          const result = await ai.models.generateContent({
            model: m,
            contents: contents.length > 0 ? contents : [{ role: 'user', parts: [{ text: 'Hello' }] }],
            config: config,
          });
          if (result && result.text) {
            responseText = result.text;
            break;
          }
        } catch (err: any) {
          lastError = err;
          console.warn(`Model ${m} temporarily unavailable:`, err?.message || err);
        }
      }

      if (!responseText && lastError) {
        throw lastError;
      }

      return res.json({ content: responseText || 'No response generated.' });
    } catch (error: any) {
      console.error('API Error:', error);
      return res.status(500).json({ error: error.message || 'Failed to generate response' });
    }
  });

  // Models endpoint
  app.get('/api/models', async (req, res) => {
    res.json({
      models: [
        { name: 'llama3:latest' },
        { name: 'mistral:7b' },
        { name: 'gemma2:9b' },
        { name: 'phi3:mini' },
        { name: 'gemini-3.8-flash' },
      ],
    });
  });

  // Create Vite server in middleware mode
  const vite = await createViteServer({
    server: { middlewareMode: true },
    appType: 'spa',
  });

  app.use(vite.middlewares);

  const PORT = 3000;
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on port ${PORT}`);
  });
}

startServer();
