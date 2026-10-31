'use strict';
// Keep research, local settings and tooling out of every Netlify publication.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const source=path.resolve(process.argv[2]||__dirname);
const output=path.resolve(process.argv[3]||path.join(__dirname,'_public'));
assert.notEqual(source,output,'Publish output must be separate from source');
const files=['index.html','phone_db.json','manifest.webmanifest','sw.js','icon-192.png','icon-512.png','apple-touch-icon.png'];
fs.mkdirSync(output,{recursive:true});
assert.ok(fs.readdirSync(output).every(f=>files.includes(f)),'Unexpected file in publish directory; inspect rather than delete');
for(const file of files)fs.copyFileSync(path.join(source,file),path.join(output,file));
assert.deepEqual(fs.readdirSync(output).sort(),files.sort());
console.log('Prepared exactly seven public runtime files at '+output);
