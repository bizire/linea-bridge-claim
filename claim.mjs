import 'dotenv/config';
import { LineaSDK } from "@consensys/linea-sdk";

// https://docs.linea.build/api/linea-sdk#claim
// process.env.L1_PK, // ХРАНИ КЛЮЧ В ENV!

// Запуск:
// вариант А: всё в .env
// node claim.mjs

// вариант Б: передать TX_HASH аргументом
// node claim.mjs 0x05ede3fdb6...b6830d1b

const INFURA_KEY = process.env.INFURA_KEY;
const L1_PK = process.env.L1_PK;
const TX_HASH = process.env.TX_HASH || process.argv[2]; // можно передать хэш аргументом

console.log('INFURA_KEY =',INFURA_KEY); 

if (!INFURA_KEY) throw new Error('Set INFURA_KEY in .env');
if (!L1_PK)      throw new Error('Set L1_PK in .env');
if (!TX_HASH)    throw new Error('Provide TX_HASH in .env or as argv: node claim.mjs <txHash>');

const l1RpcUrl_Infura = `https://mainnet.infura.io/v3/${INFURA_KEY}`;
const l2RpcUrl_Infura = `https://linea-mainnet.infura.io/v3/${INFURA_KEY}`;

const sdk = new LineaSDK(
  { network: 'linea-mainnet',
    mode: 'read-write', 
    l1RpcUrl: l1RpcUrl_Infura, 
    l2RpcUrl: l2RpcUrl_Infura, 
    l1SignerPrivateKey: L1_PK, 
    l2SignerPrivateKey: L1_PK, 
  });

  const l1Contract = sdk.getL1Contract(); 
  const l2Contract = sdk.getL2Contract(); 
  const l1ClaimingService = sdk.getL1ClaimingService();

const messages = await l2Contract.getMessagesByTransactionHash(TX_HASH); 
const message = messages[0];
console.log('messages =',message); 
console.log('messageHash =',message.messageHash);

// const messageStatus = await l1ClaimingService.getMessageStatus(messages[0].messageHash); 
// console.log('messageStatus =', messageStatus); 

const resp = await l1ClaimingService.claimMessage(messages[0]); 
console.log('resp =', resp); 

