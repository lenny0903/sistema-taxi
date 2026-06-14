const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const fs = require('fs');
const app = express();

app.use(express.json());

const client = new Client({
    authStrategy: new LocalAuth(), // ¡Importante para no perder la sesión!
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
        protocolTimeout: 60000 
    }
});

client.on('qr', (qr) => qrcode.generate(qr, { small: true }));
client.on('ready', () => console.log('¡WhatsApp conectado y listo!'));

app.post('/send-message', async (req, res) => {
    try {
        console.log("Datos recibidos:", JSON.stringify(req.body));
        
        const { number, message, filePath } = req.body;
        
        if (!number || !message) {
            return res.status(400).json({ status: 'error', error: 'Faltan campos' });
        }

        const cleanNumber = String(number).replace(/\D/g, ''); 
        const chatId = `${cleanNumber}@c.us`;

        // Lógica de envío
        if (filePath && fs.existsSync(filePath)) {
            try {
                const media = MessageMedia.fromFilePath(filePath);
                await client.sendMessage(chatId, media, { caption: message });
                console.log(`Mensaje con archivo enviado a: ${chatId}`);
            } catch (fileErr) {
                console.error("Error al enviar archivo, enviando solo texto:", fileErr);
                await client.sendMessage(chatId, message);
            }
        } else {
            await client.sendMessage(chatId, message);
            console.log(`Mensaje de texto enviado a: ${chatId}`);
        }
        
        res.status(200).json({ status: 'success' });

    } catch (err) {
        console.error("ERROR CRÍTICO EN BOT:", err);
        res.status(500).json({ status: 'error', error: err.message });
    }
});

client.initialize();
app.listen(3000, () => console.log('Servidor corriendo en puerto 3000'));