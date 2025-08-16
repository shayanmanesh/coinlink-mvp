// Test WebSocket connection with production URLs
const WebSocket = require('ws');

const environments = {
  local: 'ws://localhost:8000/ws',
  production: 'wss://coinlink-mvp-production.up.railway.app/ws',
  productionDomain: 'wss://api.coin.link/ws'
};

async function testWebSocketConnection(name, url) {
  console.log(`\n[${name}] Testing WebSocket connection to: ${url}`);
  
  return new Promise((resolve) => {
    const ws = new WebSocket(url);
    let connected = false;
    let pingReceived = false;
    
    const timeout = setTimeout(() => {
      if (!connected) {
        console.log(`[${name}] ❌ Connection timeout after 10 seconds`);
        ws.close();
        resolve(false);
      }
    }, 10000);
    
    ws.on('open', () => {
      connected = true;
      console.log(`[${name}] ✅ Connected successfully`);
      
      // Send a ping message
      const pingMessage = JSON.stringify({ type: 'ping', timestamp: new Date().toISOString() });
      console.log(`[${name}] Sending ping: ${pingMessage}`);
      ws.send(pingMessage);
      
      // Wait for response
      setTimeout(() => {
        if (pingReceived) {
          console.log(`[${name}] ✅ Ping-pong cycle completed`);
        } else {
          console.log(`[${name}] ⚠️ No pong received within 3 seconds`);
        }
        ws.close();
        clearTimeout(timeout);
        resolve(true);
      }, 3000);
    });
    
    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data.toString());
        console.log(`[${name}] Received message:`, message);
        
        if (message.type === 'pong') {
          pingReceived = true;
          console.log(`[${name}] ✅ Pong received`);
        } else if (message.type === 'ping') {
          // Server sent us a ping, respond with pong
          const pongMessage = JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() });
          console.log(`[${name}] Responding to ping with pong`);
          ws.send(pongMessage);
        }
      } catch (error) {
        console.log(`[${name}] Failed to parse message:`, error.message);
      }
    });
    
    ws.on('error', (error) => {
      console.log(`[${name}] ❌ WebSocket error:`, error.message);
      clearTimeout(timeout);
      resolve(false);
    });
    
    ws.on('close', (code, reason) => {
      console.log(`[${name}] Connection closed - Code: ${code}, Reason: ${reason || 'No reason provided'}`);
      clearTimeout(timeout);
      if (!connected) {
        resolve(false);
      }
    });
  });
}

async function runTests() {
  console.log('='.repeat(60));
  console.log('WebSocket Connection Tests');
  console.log('='.repeat(60));
  
  const results = {};
  
  // Test each environment
  for (const [name, url] of Object.entries(environments)) {
    results[name] = await testWebSocketConnection(name, url);
  }
  
  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('Test Summary:');
  console.log('='.repeat(60));
  for (const [name, success] of Object.entries(results)) {
    const status = success ? '✅ PASS' : '❌ FAIL';
    console.log(`${name}: ${status}`);
  }
  
  // Check if production URLs are configured correctly
  console.log('\n' + '='.repeat(60));
  console.log('Configuration Check:');
  console.log('='.repeat(60));
  console.log('Environment variables to set:');
  console.log('REACT_APP_API_URL=https://coinlink-mvp-production.up.railway.app');
  console.log('REACT_APP_WS_URL=wss://coinlink-mvp-production.up.railway.app/ws');
  console.log('\nOr for custom domain:');
  console.log('REACT_APP_API_URL=https://api.coin.link');
  console.log('REACT_APP_WS_URL=wss://api.coin.link/ws');
}

// Run tests
runTests().catch(console.error);