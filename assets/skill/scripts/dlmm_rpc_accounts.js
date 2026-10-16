"use strict";

// Keep one bank context and the original response order while avoiding repeated
// addresses consuming provider account limits. No splitting or extra RPC calls.
function deduplicateAccountReads(connection) {
  const read = connection.getMultipleAccountsInfoAndContext.bind(connection);
  connection.getMultipleAccountsInfoAndContext = async function(keys, config) {
    const unique = [], indexes = [], seen = new Map();
    for (const key of keys) {
      const address = key.toBase58();
      if (!seen.has(address)) { seen.set(address, unique.length); unique.push(key); }
      indexes.push(seen.get(address));
    }
    if (unique.length === keys.length) return read(keys, config);
    const result = await read(unique, config);
    if (!Array.isArray(result.value) || result.value.length !== unique.length) {
      throw new Error("Incomplete deduplicated account response");
    }
    return {...result, value: indexes.map(i => {
      const account = result.value[i];
      return account === null ? null : {...account, data: Buffer.from(account.data)};
    })};
  };
  return connection;
}
module.exports = {deduplicateAccountReads};
