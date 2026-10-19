// Private tracker; application history stays in Google Sheets.
const OWNER='aramasubban',REPO='job-puller',BRANCH='main';
const SHEET_ID='1uy2bZwnVGelp7PbFo7xltleZS1Atpqz648Wc67yDrT4';
const FEED='https://raw.githubusercontent.com/'+OWNER+'/'+REPO+'/'+BRANCH+'/data/jobs.json';
const HEADERS=['POSTING ↗','Company','Match / 100','Annual base pay','Pay check','YOUR STATUS','Role area','Location','Experience check','Applied on','Follow-up','YOUR NOTES','Listing','First seen','Last seen','Source','Work style','Application URL','Job ID','Base min','Base max','Fit evidence / gaps','Employment','Posted','Company context'];
const MIN_FIT_SCORE=50;
const STATUS=['Not Applied','Applied','Interviewing','Offer','Rejected','Not Interested'];
function book_(){return SpreadsheetApp.openById(SHEET_ID)}
function tab_(s){const b=book_();return b.getSheetByName(s)||b.insertSheet(s)}
function onOpen(){SpreadsheetApp.getUi().createMenu('Job Puller').addItem('Sync now','syncJobs').addItem('Activate tracker','activateTracker').addItem('Organize applications','refreshApplyNext_').addToUi()}
function safe_(x){const t=String(x==null?'':x);return /^[=+@]/.test(t)?"'"+t:t}
function link_(u,t){return String(u||'').startsWith('https://')?'=HYPERLINK("'+String(u).replace(/"/g,'""')+'","'+String(t).replace(/"/g,'""')+'")':safe_(t)}
function header_(s,h){s.getRange(1,1,1,h.length).setValues([h]).setBackground('#13223A').setFontColor('white').setFontWeight('bold');s.setFrozenRows(1);s.setRowHeight(1,40)}
function setupTracker(){tab_('Jobs');tab_('Applied');tab_('Run Log');refreshApplyNext_();buildDashboard_()}
function jobRow_(j,old){const o=old||[],u=j.apply_url||j.source_url||'';return [link_(u,j.title),safe_(j.company),Number(j.fit_score)||0,safe_(j.salary||'Not disclosed'),safe_(j.salary_fit||'Undisclosed — review'),o[5]||'Not Applied',safe_(j.category),safe_(j.location),safe_(j.experience_fit),o[9]||'',o[10]||'',o[11]||'','Open',o[13]||j.last_seen||'',j.last_seen||'',safe_(j.source),safe_(j.workstyle),safe_(u),safe_(j.id),j.salary_min==null?'':Number(j.salary_min),j.salary_max==null?'':Number(j.salary_max),safe_(j.match_reasons),safe_(j.employment),safe_(j.posted),safe_(j.company_context||o[24]||'')]}
function readRows_(s){return s.getLastRow()>1?s.getRange(2,1,s.getLastRow()-1,HEADERS.length).getValues().filter(r=>r[18]):[]}
function dismissed_(r){return r[5]=='Not Interested'&&!r[9]}
function archived_(r){return ['Applied','Interviewing','Offer','Rejected'].includes(r[5])||(r[5]=='Not Interested'&&!!r[9])}
function writeRows_(s,rows){
 const old=Math.max(0,s.getLastRow()-1);header_(s,HEADERS);s.showRows(2,s.getMaxRows()-1);
 if(rows.length>=s.getMaxRows())s.insertRowsAfter(s.getMaxRows(),rows.length-s.getMaxRows()+1);
 const output=rows.map(r=>{const x=r.slice();x[0]=String(x[0]).startsWith('=HYPERLINK(')?x[0]:link_(x[17],x[0]);return x});
 if(output.length)s.getRange(2,1,output.length,HEADERS.length).setValues(output);
 if(old>output.length)s.getRange(output.length+2,1,old-output.length,HEADERS.length).clearContent();
 if(s.getFilter())s.getFilter().remove();s.getRange(1,1,s.getMaxRows(),HEADERS.length).createFilter();
 s.setFrozenColumns(2);s.setColumnWidth(1,330);s.setColumnWidth(2,125);s.setColumnWidth(3,85);s.setColumnWidth(4,165);s.setColumnWidth(5,145);s.setColumnWidth(6,125);s.setColumnWidth(8,175);s.setColumnWidth(12,255);s.setColumnWidth(22,390);
 s.getRange(2,6,s.getMaxRows()-1,1).setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(STATUS,true).setAllowInvalid(false).build());
 s.getRange(2,10,s.getMaxRows()-1,2).setNumberFormat('yyyy-mm-dd');
 s.setRowHeights(2,s.getMaxRows()-1,32);s.getRange(2,1,s.getMaxRows()-1,HEADERS.length).setFontSize(9).setWrapStrategy(SpreadsheetApp.WrapStrategy.CLIP).setVerticalAlignment('middle');
 s.getRange(2,1,Math.max(1,output.length),1).setFontColor('#087E8B').setFontLine('underline');
 s.setConditionalFormatRules(STATUS.map((x,i)=>SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo(x).setBackground(['#EDF4FF','#DDF8E6','#FFF2C9','#B3F2D5','#FCE3E3','#F2F2F2'][i]).setRanges([s.getRange(2,6,s.getMaxRows()-1,1)]).build()));
}
function writeSplit_(rows){
 const unique=new Map(rows.filter(r=>r[18]).map(r=>[String(r[18]),r]));const all=Array.from(unique.values());
 const groups=[['Applied',all.filter(archived_).sort((a,b)=>Number(new Date(b[9]||0))-Number(new Date(a[9]||0)))],['Dismissed',all.filter(dismissed_)],['Jobs',all.filter(r=>!archived_(r)&&!dismissed_(r)&&Number(r[2])>=MIN_FIT_SCORE).sort((a,b)=>Number(b[2])-Number(a[2])||String(a[1]).localeCompare(String(b[1])))]];
 // Stage destination copies before removing any source records.
 groups.forEach(([name,dest])=>{const sheet=tab_(name),existing=readRows_(sheet),ids=new Set(existing.map(r=>String(r[18]))),missing=dest.filter(r=>!ids.has(String(r[18])));if(missing.length)writeRows_(sheet,existing.concat(missing))});
 groups.forEach(([name,dest])=>writeRows_(tab_(name),dest));
 tab_('Dismissed').hideSheet();
}
function refreshApplyNext_(){const lock=LockService.getScriptLock();lock.waitLock(120000);try{writeSplit_(readRows_(tab_('Jobs')).concat(readRows_(tab_('Applied')),readRows_(tab_('Dismissed'))))}finally{lock.releaseLock()}}
function syncJobs(){
 const lock=LockService.getScriptLock();if(!lock.tryLock(10000))throw new Error('Another sync is running');
 try{
 const res=UrlFetchApp.fetch(FEED,{muteHttpExceptions:true});if(res.getResponseCode()!=200)throw new Error('Job feed HTTP '+res.getResponseCode());
 const feed=JSON.parse(res.getContentText());if(!Array.isArray(feed.jobs)||!feed.sources_checked||!feed.sources_checked.length)throw new Error('No validated sources; existing applications preserved');
 const old=readRows_(tab_('Jobs')).concat(readRows_(tab_('Applied')),readRows_(tab_('Dismissed'))),byId=new Map(old.map(r=>[String(r[18]),r]));
 const seen=new Set((feed.source_status||[]).filter(x=>x.state==='OK').map(x=>x.source)),fresh=new Map(feed.jobs.filter(j=>j.id).map(j=>[String(j.id),j]));const rows=[];let added=0;
 byId.forEach((r,id)=>{if(fresh.has(id)){rows.push(jobRow_(fresh.get(id),r));fresh.delete(id)}else{const keep=r.slice();if(seen.has(String(r[15])))keep[12]='Not listed';rows.push(keep)}});
 fresh.forEach(j=>{rows.push(jobRow_(j,null));added++});writeSplit_(rows);
 const c=tab_('Coverage'),status=feed.source_status||[];const existing=c.getLastRow()>1?c.getRange(2,1,c.getLastRow()-1,8).getValues():[];const coverage=new Map(existing.filter(r=>r[1]).map(r=>[String(r[1]),r]));status.forEach(x=>{const old=coverage.get(String(x.source))||[];coverage.set(String(x.source),[x.company,x.source,x.state,x.matching||0,x.error||'',x.company_context||old[5]||'',x.careers_url||old[6]||'',new Date()])});const cv=Array.from(coverage.values());if(cv.length)c.getRange(2,1,cv.length,8).setValues(cv);c.hideSheet();
 buildDashboard_();const log=tab_('Run Log');if(!log.getLastRow())header_(log,['Synced at','Jobs','Added','Sources checked','Sources failed']);log.appendRow([new Date(),rows.length,added,feed.sources_checked.length,(feed.sources_failed||[]).length]);return {jobs:rows.length,added};
 }finally{lock.releaseLock()}
}
function buildDashboard_(){
 // Overview uses live formulas; status edits never rebuild it.
 const b=book_(),o=b.getSheetByName('Overview');
 if(!o)return;
 ['Dashboard','Company Limits','Coverage','Interviews'].forEach(n=>{const t=b.getSheetByName(n);if(t)t.hideSheet()});
}

function activateTracker(){installDailySync();refreshApplyNext_();buildDashboard_();console.log('Applied workflow activated. Daily refresh is managed by the 9 a.m. Pacific scheduled task.')}
function installDailySync(){
 const triggers=ScriptApp.getProjectTriggers();triggers.filter(t=>['syncJobs','onEdit'].includes(t.getHandlerFunction())).forEach(t=>ScriptApp.deleteTrigger(t));
 ScriptApp.newTrigger('onEdit').forSpreadsheet(book_()).onEdit().create();book_().setSpreadsheetTimeZone('America/Los_Angeles');
}
function onEdit(e){
 if(!e||!['Jobs','Applied'].includes(e.range.getSheet().getName())||e.range.getColumn()>6||e.range.getLastColumn()<6||e.range.getLastRow()<2)return;
 const lock=LockService.getScriptLock();lock.waitLock(120000);
 try{
  const b=book_(),s=e.range.getSheet();
  // Row positions remain stable: no sorting, row deletion or full-sheet rewrite.
  for(let i=Math.max(2,e.range.getRow());i<=e.range.getLastRow();i++){
   const r=s.getRange(i,1,1,HEADERS.length).getValues()[0];
   if(r[18]&&destination_(r)===s.getName())observeStatus_(b,r);
  }
  // Sweep pending statuses too, so rapid edits coalesced by Sheets still get routed.
  reconcileStatuses_(b);
 }finally{lock.releaseLock()}
}
function destination_(r){return archived_(r)?'Applied':dismissed_(r)?'Dismissed':'Jobs'}
function lastIdRow_(s,col,start){
 const ids=s.getRange(start,col,s.getMaxRows()-start+1,1).getValues().map(r=>String(r[0]||''));
 return {ids:ids,last:ids.reduce((n,id,i)=>id?i+start:n,start-1)};
}
function normalized_(x){return x instanceof Date?x.getTime():x==null?'':x}
function postedDay_(value,zone){
 if(value instanceof Date)return Utilities.formatDate(value,zone,'yyyy-MM-dd');
 const text=String(value==null?'':value).trim();
 if(/^\d{4}-\d{2}-\d{2}(?:$|[T ])/.test(text))return text.slice(0,10);
 const named=text.match(/^([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})$/);
 if(named){const month=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'].indexOf(named[1].slice(0,3).toLowerCase())+1;if(month&&Number(named[2])>=1&&Number(named[2])<=31)return named[3]+'-'+String(month).padStart(2,'0')+'-'+named[2].padStart(2,'0');}
 return null;
}
function sameRecord_(a,b,zone){return a.slice(1,25).every((x,i)=>{const y=b[i+1];if(normalized_(x)===normalized_(y))return true;if(i+1!==23)return false;const left=postedDay_(x,zone||'America/Los_Angeles'),right=postedDay_(y,zone||'America/Los_Angeles');return left!==null&&left===right;})}
function moveRecord_(b,s,row){
 let r=s.getRange(row,1,1,HEADERS.length).getValues()[0];if(!r[18])return false;
 const name=destination_(r);if(name===s.getName())return false;
 const target=b.getSheetByName(name);if(!target)throw new Error('Missing destination '+name);
 const index=lastIdRow_(target,19,2),existing=index.ids.indexOf(String(r[18]));
 const dest=existing>=0?existing+2:index.last+1;
 if(dest>target.getMaxRows())target.insertRowsAfter(target.getMaxRows(),100);
 if(r[5]==='Applied'&&!r[9]){s.getRange(row,10).setValue(new Date());r=s.getRange(row,1,1,HEADERS.length).getValues()[0]}
 const zone=b.getSpreadsheetTimeZone();
 const write=record=>{const out=record.slice();out[0]=link_(out[17],out[0]);target.getRange(dest,1,1,HEADERS.length).setValues([out]);SpreadsheetApp.flush();if(!sameRecord_(record,target.getRange(dest,1,1,HEADERS.length).getValues()[0],zone))throw new Error('Destination verification failed; source preserved')};
 // Destination first. If a user changes another field during the write, copy the latest record.
 write(r);
 const latest=s.getRange(row,1,1,HEADERS.length).getValues()[0];
 if(String(latest[18])!==String(r[18]))return false;
 if(!sameRecord_(latest,r,zone)){
  if(destination_(latest)!==name){if(existing<0){target.getRange(dest,1,1,HEADERS.length).clearContent();target.hideRows(dest)}return false;}
  r=latest;write(r);
 }
 s.getRange(row,1,1,HEADERS.length).clearContent();
 s.hideRows(row);target.showRows(dest);
 observeStatus_(b,r);
 return true;
}
function reconcileStatuses_(b){
 let moved=0;const failures=new Map();
 for(let pass=0;pass<2;pass++){
  let changed=0;
  ['Jobs','Applied'].forEach(name=>{
   const s=b.getSheetByName(name),statuses=s.getRange(2,6,s.getMaxRows()-1,5).getValues();
   statuses.forEach((v,i)=>{if(v[0]&&((name==='Jobs'&&v[0]!=='Not Applied')||(name==='Applied'&&(v[0]==='Not Applied'||(v[0]==='Not Interested'&&!v[4]))))){const key=name+'!'+(i+2);try{if(moveRecord_(b,s,i+2)){changed++;moved++}failures.delete(key)}catch(error){failures.set(key,String(error));console.error('Status move pending; source preserved: '+key+' '+error)}}});
  });
  if(!changed)break;
 }
 if(failures.size)console.error('Pending status rows: '+JSON.stringify(Array.from(failures.entries())));
 return moved;
}
function observeStatus_(b,r){
 const o=b.getSheetByName('Overview');if(!o)return;
 const index=lastIdRow_(o,14,23),found=index.ids.indexOf(String(r[18]));
 if(found<0&&r[5]!=='Interviewing')return;
 const row=found<0?index.last+1:found+23;
 if(row>o.getMaxRows())o.insertRowsAfter(o.getMaxRows(),100);
 if(found<0){
  const v=[r[1],link_(r[17],r[0]),'', 'Awaiting details','','','','','','','',new Date(),'',r[18],r[17]];
  o.getRange(row,1,1,2).setValues([v.slice(0,2)]);
  o.getRange(row,4,1,5).setValues([v.slice(3,8)]);
  o.getRange(row,10,1,6).setValues([v.slice(9,15)]);
  o.getRange(23,4,1,8).copyTo(o.getRange(row,4,1,8),SpreadsheetApp.CopyPasteType.PASTE_FORMAT,false);
  o.getRange(23,4).copyTo(o.getRange(row,4),SpreadsheetApp.CopyPasteType.PASTE_DATA_VALIDATION,false);
 }
 const previous=o.getRange(row,13).getValue();
 if(previous===r[5]&&r[5]!=='Interviewing')return;
 if(previous&&previous!==r[5]){const h=b.getSheetByName('Status History');if(h)h.appendRow([new Date(),r[1],r[0],previous,r[5],r[18],'Live status edit'])}
 if(r[5]==='Interviewing'){
  if(!o.getRange(row,12).getValue())o.getRange(row,12).setValue(new Date());
  o.showRows(row);
 }else o.hideRows(row);
 o.getRange(row,13).setValue(r[5]);
}
function repairPendingStatuses(){
 const lock=LockService.getScriptLock();lock.waitLock(120000);
 try{const count=reconcileStatuses_(book_());console.log('Pending statuses reconciled: '+count)}finally{lock.releaseLock()}
}

function verifyRapidStatusFix(){
 const b=book_(),s=b.getSheetByName('Jobs'),start=Date.now();
 const snapshot=()=>['Jobs','Applied','Dismissed'].flatMap(n=>readRows_(b.getSheetByName(n))).map(r=>r.map((x,i)=>i===23?(postedDay_(x,b.getSpreadsheetTimeZone())||normalized_(x)):normalized_(x))).sort((a,b)=>String(a[18]).localeCompare(String(b[18])));
 const before=snapshot(),applied=readRows_(b.getSheetByName('Applied')).find(r=>r[5]==='Applied'&&r[9]&&r[1]==='Amazon')||readRows_(b.getSheetByName('Applied')).find(r=>r[5]==='Applied'&&r[9]),dismissed=readRows_(b.getSheetByName('Dismissed')).slice(0,2);
 if(!applied||dismissed.length!==2)throw new Error('Existing records unavailable; no test changes made');
 const probes=[applied].concat(dismissed),first=lastIdRow_(s,19,2).last+1;
 probes.forEach((r,i)=>{const out=r.slice();out[0]=link_(out[17],out[0]);s.getRange(first+i,1,1,HEADERS.length).setValues([out])});
 // A single event must route all three pending edits, without shifting later rows.
 onEdit({range:s.getRange(first,6)});
 const after=snapshot();
 if(JSON.stringify(before)!==JSON.stringify(after))throw new Error('Verification mismatch; inspect staged rows before further changes');
 const ids=after.map(r=>String(r[18]));if(new Set(ids).size!==ids.length)throw new Error('Duplicate IDs after routing');
 if(probes.some((_,i)=>s.getRange(first+i,19).getValue()))throw new Error('Pending source record remains');
 console.log('PASS: 3 consecutive statuses routed in one callback; '+after.length+' records unchanged; no duplicate IDs; all notes/statuses/dates/links preserved. Elapsed '+((Date.now()-start)/1000).toFixed(1)+'s');
}

function verifyPostedDatePatch(){const a=Array(25).fill(""),b=a.slice();a[23]="July  8, 2026";b[23]=Utilities.parseDate("2026-07-08","America/Los_Angeles","yyyy-MM-dd");if(!sameRecord_(a,b,"America/Los_Angeles"))throw new Error("Posted-date conversion rejected");b[11]="Changed private note";if(sameRecord_(a,b,"America/Los_Angeles"))throw new Error("Private-field mismatch accepted");console.log("PASS: posting-date conversion accepted; private notes remain strict.")}
