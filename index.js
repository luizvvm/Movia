// index.js - Versão Completa e Atualizada

// 1. Importar todas as bibliotecas necessárias
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fetch = require('node-fetch'); // Usado para se comunicar com o backend Python/Flask

// 2. Configurar o cliente do WhatsApp com a estratégia de "memória local" (LocalAuth)
// Isso cria a pasta .wwebjs_auth para salvar a sessão e evitar escanear o QR Code toda vez.
const client = new Client({
    authStrategy: new LocalAuth()
});

console.log('INFO: Iniciando o cliente do WhatsApp...');

// 3. Evento para gerar o QR Code (só acontece na primeira vez)
client.on('qr', (qr) => {
    console.log('QR Code recebido! Escaneie com seu celular de teste.');
    qrcode.generate(qr, { small: true });
});

// 4. Evento para confirmar que a conexão foi bem-sucedida
client.on('ready', () => {
    console.log('SUCESSO: Cliente pronto e conectado ao WhatsApp!');
    console.log('Aguardando mensagens...');
});

// 5. Evento principal: acontece toda vez que uma nova mensagem é recebida
client.on('message', async (message) => {
    const userMessage = message.body;
    const userPhone = message.from;

    // Ignora mensagens que não são de um chat individual, que estão vazias ou que foram enviadas por nós mesmos.
    if (!userPhone || userMessage === '' || message.fromMe) {
        return;
    }

    console.log(`[WhatsApp] Mensagem recebida de ${userPhone}: "${userMessage}"`);

    try {
        // A. Envia a mensagem do usuário para o nosso "Cérebro" (backend Flask)
        const response = await fetch('http://localhost:10000/process-message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                from_number: userPhone,
                message_body: userMessage
            })
        });

        // Verifica se a resposta do servidor foi bem-sucedida
        if (!response.ok) {
            throw new Error(`O servidor Flask respondeu com erro: ${response.statusText}`);
        }

        const data = await response.json();
        const moviaReply = data.reply;

        // B. Recebe a resposta do Cérebro e envia de volta para o usuário
        if (moviaReply) {
            console.log(`[Movia] Enviando resposta para ${userPhone}: "${moviaReply.substring(0, 60)}..."`);
            client.sendMessage(userPhone, moviaReply);
        } else {
             console.log('[Movia] Nenhuma resposta foi gerada pelo backend.');
        }

    } catch (error) {
        console.error('ERRO CRÍTICO: Não foi possível conectar com o backend Flask:', error);
        // Envia uma mensagem de erro amigável para o usuário
        client.sendMessage(userPhone, '🤖 Desculpe, estou com um problema técnico para me conectar ao meu cérebro. Tente novamente em um instante, por favor.');
    }
});

// 6. Inicia o cliente
client.initialize();