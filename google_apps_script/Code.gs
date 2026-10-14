// Private Google Sheets tracker; public GitHub contains employer job listings only.
const OWNER='aramasubban', REPO='job-puller', BRANCH='main';
const FEED='https://raw.githubusercontent.com/'+OWNER+'/'+REPO+'/'+BRANCH+'/data/jobs.json';
const HEADERS=['POSTING ↗','Company','Match / 100','Annual base pay','Pay check','YOUR STATUS','Role area','Location','Experience check','Applied on','Follow-up','YOUR NOTES','Listing','First seen','Last seen','Source','Work style','Application URL','Job ID','Base min','Base max','Why it matches','Employment','Posted'];
const STATUS=['Not Applied','Applied','Interviewing','Offer','Rejected','Not Interested'];
function tab_(s){const b=SpreadsheetApp.getActiveSpreadsheet();return b.getSheetByName(s)||b.insertSheet(s)}
function onOpen(){SpreadsheetApp.getUi().createMenu('Job Puller').addItem('Sync now','syncJobs').addItem('Activate daily sync','activateTracker').addItem('Set up tracker','setupTracker').addItem('Refresh shortlist','refreshApplyNext_').addToUi()}
function safe_(x){const t=String(x==null?'':x);return /^[=+@]/.test(t)?"'"+t:t}
function link_(u,t){return /^https:\/\/[A-Za-z0-9.-]+\//.test(u||'')?'=HYPERLINK("'+String(u).replace(/"/g,'""')+'","'+String(t).replace(/"/g,'""')+'")':safe_(t)}
function header_(s,h){s.getRange(1,1,1,h.length).setValues([h]).setBackground('#13223A').setFontColor('white').setFontWeight('bold');s.setFrozenRows(1);s.setRowHeight(1,40)}
function setupTracker(){
 const s=tab_('Jobs');tab_('Apply Next');tab_('Dashboard');tab_('Coverage');tab_('Run Log');
 header_(s,HEADERS);s.setFrozenColumns(2);s.setColumnWidth(1,370);s.setColumnWidth(2,145);s.setColumnWidth(3,115);s.setColumnWidth(4,175);s.setColumnWidth(5,165);s.setColumnWidth(6,140);s.setColumnWidth(8,175);s.setColumnWidth(12,255);
 s.getRange(2,6,s.getMaxRows()-1,1).setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(STATUS,true).setAllowInvalid(false).build());
 s.getRange(2,10,s.getMaxRows()-1,2).setNumberFormat('yyyy-mm-dd');
 s.setConditionalFormatRules(STATUS.map((x,i)=>SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo(x).setBackground(['#EDF4FF','#DDF8E6','#FFF2C9','#B3F2D5','#FCE3E3','#F2F2F2'][i]).setRanges([s.getRange(2,6,s.getMaxRows()-1,1)]).build()));
 buildDashboard_();refreshApplyNext_();
}
function jobRow_(j,old){
 const o=old||[],u=j.apply_url||j.source_url||'';
 return [link_(u,j.title),safe_(j.company),Number(j.fit_score)||0,safe_(j.salary||'Not disclosed'),safe_(j.salary_fit||'Undisclosed — review'),o[5]||'Not Applied',safe_(j.category),safe_(j.location),safe_(j.experience_fit),o[9]||'',o[10]||'',o[11]||'','Open',o[13]||j.last_seen||'',j.last_seen||'',safe_(j.source),safe_(j.workstyle),safe_(u),safe_(j.id),j.salary_min==null?'':Number(j.salary_min),j.salary_max==null?'':Number(j.salary_max),safe_(j.match_reasons),safe_(j.employment),safe_(j.posted)];
}
function syncJobs(){
 const lock=LockService.getDocumentLock();if(!lock.tryLock(10000))throw new Error('Another sync is running');
 try{
  const res=UrlFetchApp.fetch(FEED,{muteHttpExceptions:true});
  if(res.getResponseCode()!=200)throw new Error('GitHub job feed not ready: HTTP '+res.getResponseCode());
  const feed=JSON.parse(res.getContentText());
  if(!Array.isArray(feed.jobs)||!feed.sources_checked||!feed.sources_checked.length)throw new Error('No validated sources in feed; existing applications preserved');
  const s=tab_('Jobs');if(s.getRange(1,1).getValue()!==HEADERS[0])setupTracker();
  const count=Math.max(0,s.getLastRow()-1),old=count?s.getRange(2,1,count,24).getValues():[];
  const byId=new Map(old.filter(r=>r[18]).map(r=>[String(r[18]),r]));
  const seen=new Set(feed.sources_checked),fresh=new Map(feed.jobs.filter(j=>j.id).map(j=>[String(j.id),j]));
  const rows=[];let added=0;
  byId.forEach((r,id)=>{if(fresh.has(id)){rows.push(jobRow_(fresh.get(id),r));fresh.delete(id)}else{const keep=r.slice();if(seen.has(String(r[15])))keep[12]='Not listed';rows.push(keep)}});
  fresh.forEach(j=>{rows.push(jobRow_(j,null));added++});
  rows.sort((a,b)=>Number(b[2])-Number(a[2]));
  if(rows.length>=s.getMaxRows())s.insertRowsAfter(s.getMaxRows(),rows.length-s.getMaxRows()+1);
  if(rows.length)s.getRange(2,1,rows.length,24).setValues(rows);
  if(count>rows.length)s.getRange(rows.length+2,1,count-rows.length,24).clearContent();
  s.getRange(2,1,Math.max(rows.length,1),1).setFontColor('#087E8B').setFontLine('underline');
  if(s.getFilter())s.getFilter().remove();s.getRange(1,1,Math.max(2,rows.length+1),24).createFilter();
  const c=tab_('Coverage');c.clearContents();const status=feed.source_status||[];
  header_(c,['Employer','Source','Status','Matches','Error']);if(status.length)c.getRange(2,1,status.length,5).setValues(status.map(x=>[x.company,x.source,x.state,x.matching||0,x.error||'']));
  c.setColumnWidth(1,180);c.setColumnWidth(2,235);c.setColumnWidth(3,150);c.setColumnWidth(5,390);
  refreshApplyNext_();buildDashboard_();
  const log=tab_('Run Log');if(log.getLastRow()==0)header_(log,['Synced at','Jobs','Added','Sources checked','Sources failed']);
  log.appendRow([new Date(),rows.length,added,feed.sources_checked.length,(feed.sources_failed||[]).length]);
  return {jobs:rows.length,added};
 }finally{lock.releaseLock()}
}
function refreshApplyNext_(){
 const jobs=tab_('Jobs'),s=tab_('Apply Next');s.clearContents();header_(s,['CLICK POSTING ↗','Company','Match','Annual pay','Location','Experience','Why this fits']);
 const n=jobs.getLastRow()-1;if(n<1)return;
 const rows=jobs.getRange(2,1,n,24).getValues().filter(r=>r[5]=='Not Applied'&&r[12]=='Open').sort((a,b)=>Number(b[2])-Number(a[2])).slice(0,100);
 if(rows.length)s.getRange(2,1,rows.length,7).setValues(rows.map(r=>[link_(r[17],r[0]),r[1],r[2],r[3],r[7],r[8],r[21]]));
 s.setColumnWidth(1,370);s.setColumnWidth(2,165);s.setColumnWidth(4,190);s.setColumnWidth(5,185);s.setColumnWidth(7,275);
}
function buildDashboard_(){
 const s=tab_('Dashboard');s.getRange('A1:L26').getMergedRanges().forEach(x=>x.breakApart());s.clearContents();
 s.getRange('A1:L2').merge().setValue('BAY AREA  /  ENGINEERING JOB SEARCH').setBackground('#13223A').setFontColor('white').setFontWeight('bold').setFontSize(19);
 s.getRange('A3:L3').merge().setValue('MECHANICAL • ROBOTICS • BATTERY / EV • MANUFACTURING EQUIPMENT  |  MAY 2027').setBackground('#EAF3F4');
 const cards=[['A5:C5','A6:C8','OPEN POSITIONS','=COUNTIF(Jobs!M2:M,"Open")'],['D5:F5','D6:F8','READY TO APPLY','=COUNTIFS(Jobs!F2:F,"Not Applied",Jobs!M2:M,"Open")'],['G5:I5','G6:I8','APPLICATIONS','=COUNTIF(Jobs!F2:F,"Applied")'],['J5:L5','J6:L8','INTERVIEWS','=COUNTIF(Jobs!F2:F,"Interviewing")']];
 cards.forEach(v=>{s.getRange(v[0]).merge().setValue(v[2]).setBackground('#E7EDF4').setFontColor('#52667A').setFontWeight('bold');s.getRange(v[1]).merge().setFormula(v[3]).setBackground('#F6F9FC').setFontColor('#13223A').setFontSize(28).setFontWeight('bold')});
 s.getRange('A10:L10').merge().setValue('APPLICATION PIPELINE').setBackground('#13223A').setFontColor('white').setFontWeight('bold');
 const lines=[['Applied','=COUNTIF(Jobs!F2:F,"Applied")'],['Interviewing','=COUNTIF(Jobs!F2:F,"Interviewing")'],['Offers','=COUNTIF(Jobs!F2:F,"Offer")'],['Employers scanned','=COUNTIF(Coverage!C2:C,"OK*")'],['Employer errors','=COUNTIF(Coverage!C2:C,"ERROR")']];
 lines.forEach((v,i)=>{s.getRange(12+i,1).setValue(v[0]);s.getRange(12+i,3).setFormula(v[1])});
 s.getRange('A20:L21').merge().setValue('Click the job title to open the employer posting • Update YOUR STATUS in Jobs • Check Coverage for source errors').setBackground('#EAF3F4');
 s.setColumnWidths(1,12,93);
}
function activateTracker(){syncJobs();installDailySync()}
function installDailySync(){ScriptApp.getProjectTriggers().filter(t=>t.getHandlerFunction()=='syncJobs').forEach(ScriptApp.deleteTrigger);ScriptApp.newTrigger('syncJobs').timeBased().atHour(9).everyDays(1).inTimezone('America/Los_Angeles').create()}
function onEdit(e){if(!e||e.range.getSheet().getName()!=='Jobs'||e.range.getColumn()!=6||e.range.getRow()<2)return;const s=e.range.getSheet();if(e.value=='Applied'&&!s.getRange(e.range.getRow(),10).getValue())s.getRange(e.range.getRow(),10).setValue(new Date());refreshApplyNext_();buildDashboard_()}
