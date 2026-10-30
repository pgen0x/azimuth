"use strict";
const assert = require('node:assert/strict');
const {deduplicateAccountReads} = require('./dlmm_rpc_accounts');
(async () => {
  const key = n => ({toBase58: () => String(n)});
  const keys = [1,2,3,4,0,0,0,0].map(key), config = {commitment:'confirmed',minContextSlot:100};
  let calls=0;
  const connection={async getMultipleAccountsInfoAndContext(input, passed) {
    calls++; assert.equal(passed, config); assert.equal(input.length,5);
    return {context:{slot:101},value:input.map(k=>k.toBase58()==='3'?null:{lamports:1,data:Buffer.from(k.toBase58())})};
  }};
  deduplicateAccountReads(connection);
  const result=await connection.getMultipleAccountsInfoAndContext(keys,config);
  assert.equal(calls,1);assert.equal(result.context.slot,101);assert.equal(result.value.length,8);
  assert.equal(result.value[2],null);assert.equal(result.value[7].data.toString(),'0');
  result.value[4].data[0]=99;assert.equal(result.value[5].data.toString(),'0');
  const unique=[1,2,3,4,5].map(key);
  await connection.getMultipleAccountsInfoAndContext(unique,config);assert.equal(calls,2);
  const failing=deduplicateAccountReads({async getMultipleAccountsInfoAndContext(){throw Error('provider down')}});
  await assert.rejects(failing.getMultipleAccountsInfoAndContext(keys,config),/provider down/);
  const short=deduplicateAccountReads({async getMultipleAccountsInfoAndContext(){return {context:{slot:1},value:[]}}});
  await assert.rejects(short.getMultipleAccountsInfoAndContext(keys,config),/Incomplete/);
  console.log('Account dedup preserves order, nulls, context, config, buffer isolation and errors; one RPC.');
})().catch(e=>{console.error(e);process.exitCode=1});
