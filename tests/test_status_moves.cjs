const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const context={console,Date,Map,Set,SpreadsheetApp:{flush(){}},Utilities:{formatDate(value,zone){const parts=new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(value);const p=Object.fromEntries(parts.map(x=>[x.type,x.value]));return `${p.year}-${p.month}-${p.day}`;}}};
vm.createContext(context);vm.runInContext(fs.readFileSync('google_apps_script/Code.gs','utf8'),context);
function row(id,status='Applied'){const r=Array(25).fill('');r[0]='Mechanical Engineer';r[1]='Amazon';r[2]=66;r[5]=status;r[9]=status==='Applied'?new Date('2026-10-19T18:00:00Z'):'';r[11]='Private note';r[13]='2026-10-19T16:07:33Z';r[17]='https://example.com/'+id;r[18]=id;r[23]='July  8, 2026';return r;}
const original=row('test');const converted=original.slice();converted[23]=new Date('2026-07-08T07:00:00Z');
assert(context.sameRecord_(original,converted,'America/Los_Angeles'));
converted[11]='different note';assert(!context.sameRecord_(original,converted,'America/Los_Angeles'));converted[11]=original[11];
converted[5]='Rejected';assert(!context.sameRecord_(original,converted,'America/Los_Angeles'));converted[5]=original[5];
converted[13]='changed first-seen';assert(!context.sameRecord_(original,converted,'America/Los_Angeles'));converted[13]=original[13];
converted[23]=new Date('2026-07-09T07:00:00Z');assert(!context.sameRecord_(original,converted,'America/Los_Angeles'));
class Sheet{
 constructor(name){this.name=name;this.rows=Array.from({length:20},()=>Array(25).fill(''));this.hidden=new Set();}
 getMaxRows(){return this.rows.length;}
 getName(){return this.name;}
 getRange(row,col,n=1,m=1){const s=this;return {getValues(){return Array.from({length:n},(_,i)=>Array.from({length:m},(_,j)=>s.rows[row-1+i]?.[col-1+j]??''));},getValue(){return s.rows[row-1][col-1];},setValue(v){s.rows[row-1][col-1]=v;},setValues(values){values.forEach((r,i)=>r.forEach((v,j)=>{if(s.name!=='Jobs'&&col-1+j===23&&typeof v==='string'&&v.startsWith('July'))v=new Date('2026-07-08T07:00:00Z');s.rows[row-1+i][col-1+j]=v;}));},clearContent(){for(let i=0;i<n;i++)for(let j=0;j<m;j++)s.rows[row-1+i][col-1+j]='';}};}
 hideRows(row){this.hidden.add(row);}showRows(row){this.hidden.delete(row);}
}
const jobs=new Sheet('Jobs'),applied=new Sheet('Applied'),dismissed=new Sheet('Dismissed');
const tabs={Jobs:jobs,Applied:applied,Dismissed:dismissed};const book={getSheetByName(n){return tabs[n];},getSpreadsheetTimeZone(){return 'America/Los_Angeles';}};
const records=[row('one'),row('two','Not Interested'),row('three','Not Interested')];records.forEach((r,i)=>jobs.rows[i+1]=r.slice());
for(let i=0;i<3;i++)assert(context.moveRecord_(book,jobs,i+2));
assert(records.every((_,i)=>jobs.rows[i+1][18]===''));assert.equal(applied.rows[1][18],'one');assert.equal(dismissed.rows[1][18],'two');assert.equal(dismissed.rows[2][18],'three');
assert.equal(applied.rows[1][11],'Private note');assert.equal(applied.rows[1][13],records[0][13]);assert.equal(new Set([...applied.rows,...dismissed.rows].map(r=>r[18]).filter(Boolean)).size,3);
console.log('PASS: posted-date conversion accepted; changed day/status/notes/first-seen rejected; Applied + two Not Interested moves complete with exact private fields and unique IDs.');
// One genuinely unverifiable destination must not prevent later queued moves.
const jobs2=new Sheet('Jobs'),applied2=new Sheet('Applied'),dismissed2=new Sheet('Dismissed');
const tabs2={Jobs:jobs2,Applied:applied2,Dismissed:dismissed2},book2={getSheetByName(n){return tabs2[n];},getSpreadsheetTimeZone(){return 'America/Los_Angeles';}};
const rawRange=applied2.getRange.bind(applied2);
applied2.getRange=function(...args){const range=rawRange(...args),write=range.setValues;range.setValues=function(values){write(values);if(values[0]?.[18]==='bad')applied2.rows[args[0]-1][11]='Simulated destination corruption';};return range;};
jobs2.rows[1]=row('bad');jobs2.rows[2]=row('four','Not Interested');jobs2.rows[3]=row('five','Not Interested');
const realError=console.error;console.error=()=>{};const moved=context.reconcileStatuses_(book2);console.error=realError;
assert.equal(moved,2);assert.equal(jobs2.rows[1][18],'bad');assert.equal(jobs2.rows[1][11],'Private note');assert.equal(jobs2.rows[2][18],'');assert.equal(jobs2.rows[3][18],'');
assert.equal(dismissed2.rows[1][18],'four');assert.equal(dismissed2.rows[2][18],'five');
console.log('PASS: a failed verification preserves its source and does not block two later Not Interested edits.');
