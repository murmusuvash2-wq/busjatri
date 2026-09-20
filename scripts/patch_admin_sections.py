#!/usr/bin/env python3
"""Admin panel restructure (2026-09-20):
- Split 'Reports' into 3 sections: Time Updates / Issue Reports / New Buses
- New Buses: Approve -> community_buses.json + rebuild; duplicate detection
- AM/PM time formatting everywhere
- apply-overrides.yml: also merge community buses"""
import io

def rep(s, old, new, label, count=1):
    n = s.count(old)
    assert n == count, '%s: expected %d, found %d' % (label, count, n)
    return s.replace(old, new)

NAV_OLD = '    <div class="nav-item" data-view="reports"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>Reports <span class="tag g" id="repBadge" style="display:none;margin-left:auto">0</span></div>'
NAV_NEW = ('''    <div class="nav-item" data-view="reports"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>Time Updates <span class="tag g" id="repBadge" style="display:none;margin-left:auto">0</span></div>
    <div class="nav-item" data-view="issues"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>Issues <span class="tag o" id="issBadge" style="display:none;margin-left:auto">0</span></div>
    <div class="nav-item" data-view="newbuses"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M10 9v6M14 9v6"/></svg>New Buses <span class="tag g" id="busBadge" style="display:none;margin-left:auto">0</span></div>''')

STAT_OLD = '          <div class="stat"><div class="lbl">Pending Reports</div><div class="val" id="stReports">\u2014</div><div class="sub">data/time-reports.json</div></div>'
STAT_NEW = ('''          <div class="stat"><div class="lbl">Time Updates</div><div class="val" id="stReports">\u2014</div><div class="sub">pending user times</div></div>
          <div class="stat"><div class="lbl">Issue Reports</div><div class="val" id="stIssues">\u2014</div><div class="sub">bus-stopped / route</div></div>
          <div class="stat"><div class="lbl">New Buses</div><div class="val" id="stBusesNew">\u2014</div><div class="sub">contributions pending</div></div>''')

QA_OLD = "              <button class=\"btn btn-ghost\" onclick=\"go('reports')\">Check User Reports</button>"
QA_NEW = ('''              <button class="btn btn-ghost" onclick="go('reports')">Time Updates</button>
              <button class="btn btn-ghost" onclick="go('issues')">Issue Reports</button>
              <button class="btn btn-ghost" onclick="go('newbuses')">New Buses</button>''')

SEC_OLD = ('''      <!-- REPORTS -->
      <section id="view-reports" class="view" style="display:none">
        <div class="card">
          <h3>\U0001f41e User Time Reports</h3>
          <div class="hint" style="margin:0 0 14px">Site se aaye reports yahan dikhte hain (Google Sheet se). <b>Approve</b> = time site pe live. <b>Fix</b> = khud edit karke save. <b>Reject</b> = nikaal do.</div>
          <div class="scrollbox" style="max-height:620px"><table><thead><tr><th>Bus</th><th>Route</th><th>Time (current \u2192 correct)</th><th>Note</th><th>When</th><th style="width:180px">Actions</th></tr></thead><tbody id="reportRows"></tbody></table></div>
        </div>
      </section>''')
SEC_NEW = ('''      <!-- TIME UPDATES -->
      <section id="view-reports" class="view" style="display:none">
        <div class="card">
          <h3>\u23f1 User Time Updates</h3>
          <div class="hint" style="margin:0 0 14px">Stoppage time ke corrections yahan aate hain. <b>Approve</b> = time site pe live. <b>Fix</b> = khud edit karke save. <b>Reject</b> = nikaal do.</div>
          <div class="scrollbox" style="max-height:620px"><table><thead><tr><th>Bus</th><th>Route</th><th>Time (current \u2192 correct)</th><th>Note</th><th>When</th><th style="width:180px">Actions</th></tr></thead><tbody id="reportRows"></tbody></table></div>
        </div>
      </section>

      <!-- ISSUE REPORTS -->
      <section id="view-issues" class="view" style="display:none">
        <div class="card">
          <h3>\U0001f6d1 Issue Reports</h3>
          <div class="hint" style="margin:0 0 14px">Bus band / route badal gayi \u2014 ye reports yahan. <b>Handled</b> = dekh liya. <b>Fix</b> = bus editor mein kholo. <b>Reject</b> = nikaal do.</div>
          <div class="scrollbox" style="max-height:620px"><table><thead><tr><th>Bus</th><th>Route</th><th>Type</th><th>Note</th><th>When</th><th style="width:190px">Actions</th></tr></thead><tbody id="issueRows"></tbody></table></div>
        </div>
      </section>

      <!-- NEW BUSES -->
      <section id="view-newbuses" class="view" style="display:none">
        <div class="card">
          <h3>\U0001f68c New Bus Contributions</h3>
          <div class="hint" style="margin:0 0 14px">Form se aayi nayi buses. <b>Approve</b> = site pe live (community_buses.json + rebuild, 3-5 min). Duplicate ho to warning dikhega. <b>Reject</b> = nikaal do. <i>invalid</i> wali rows galat data hain.</div>
          <div class="scrollbox" style="max-height:620px"><table><thead><tr><th>Bus</th><th>Route</th><th>Times</th><th>Stops</th><th>Contributor</th><th>When</th><th style="width:170px">Actions</th></tr></thead><tbody id="busRows"></tbody></table></div>
        </div>
      </section>''')

GO_T_OLD = "$('#viewTitle').textContent=({dash:'Dashboard',buses:'Bus Times',blog:'Blog Manager',reports:'User Reports',settings:'Settings'})[v];"
GO_T_NEW = "$('#viewTitle').textContent=({dash:'Dashboard',buses:'Bus Times',blog:'Blog Manager',reports:'Time Updates',issues:'Issue Reports',newbuses:'New Buses',settings:'Settings'})[v];"
GO_C_OLD = "$('#crumb').textContent='BusJatri / '+({dash:'overview',buses:'manage times',blog:'content',reports:'user reports',settings:'config'})[v];"
GO_C_NEW = "$('#crumb').textContent='BusJatri / '+({dash:'overview',buses:'manage times',blog:'content',reports:'time updates',issues:'issue reports',newbuses:'new buses',settings:'config'})[v];"
GO_L_OLD = "  if(v==='dash')loadDash();if(v==='blog')loadBlog();if(v==='reports')loadReports();"
GO_L_NEW = "  if(v==='dash')loadDash();if(v==='blog')loadBlog();if(v==='reports')loadReports('time');if(v==='issues')loadReports('issues');if(v==='newbuses')loadNewBuses();"

DASH_OLD = "  try{const rp=JSON.parse(await rawGet('data/time-reports.json'));const pend=rp.filter(r=>r.status!=='done').length;$('#stReports').textContent=pend;const bb=$('#repBadge');if(bb){bb.style.display=pend?'inline-flex':'none';bb.textContent=pend}}catch(e){$('#stReports').textContent='0'}"
DASH_NEW = ('''  const tkd=rptTok();
  if(tkd){
    try{const r=await fetch(RPT_URL+'?action=list&token='+encodeURIComponent(tkd));const j=await r.json();const fresh=(j.rows||[]).filter(x=>x.status==='new');
      const tc=fresh.filter(x=>x.type==='add-time').length;const ic=fresh.length-tc;
      $('#stReports').textContent=tc;$('#stIssues').textContent=ic;setBadge('repBadge',tc);setBadge('issBadge',ic);}catch(e){$('#stReports').textContent='\u2014';$('#stIssues').textContent='\u2014'}
    try{const r=await fetch(RPT_URL+'?action=list-buses&token='+encodeURIComponent(tkd));const j=await r.json();const bc=(j.rows||[]).filter(x=>x.status==='new').length;
      $('#stBusesNew').textContent=bc;setBadge('busBadge',bc);}catch(e){$('#stBusesNew').textContent='\u2014'}
  }else{$('#stReports').textContent='\u2014';$('#stIssues').textContent='\u2014';$('#stBusesNew').textContent='\u2014'}''')

LR_START = 'async function loadReports(){'
LR_END = "  tb.querySelectorAll('button[data-a]').forEach(btn=>btn.onclick=()=>rptAction(btn.dataset.a,+btn.dataset.i));\n}"
LR_NEW = ('''async function loadReports(mode){
  mode=mode||'time';
  const timeMode=mode==='time';
  const tb=$(timeMode?'#reportRows':'#issueRows');
  const tk=rptTok();
  if(!tk){tb.innerHTML='<tr><td colspan="6" class="empty">Pehle Settings mein <b>Report Receiver Token</b> daalo (bj-adm- wala), phir yahan wapas aao.</td></tr>';return}
  tb.innerHTML='<tr><td colspan="6" class="empty">Loading\u2026</td></tr>';
  let rows=[];
  try{
    const r=await fetch(RPT_URL+'?action=list&token='+encodeURIComponent(tk));
    const j=await r.json();
    rows=j.rows||[];
  }catch(e){tb.innerHTML='<tr><td colspan="6" class="empty">Load fail: '+esc(e.message)+' \u2014 thodi der baad phir kholo</td></tr>';return}
  const fresh=rows.filter(x=>x.status==='new');
  const timeRows=fresh.filter(x=>x.type==='add-time');
  const issRows=fresh.filter(x=>x.type!=='add-time');
  REPORTS=timeRows;ISSUES=issRows;
  setBadge('repBadge',timeRows.length);
  setBadge('issBadge',issRows.length);
  const st=$('#stReports');if(st)st.textContent=timeRows.length;
  const st2=$('#stIssues');if(st2)st2.textContent=issRows.length;
  const done=rows.length-fresh.length;
  if(timeMode){
    tb.innerHTML=timeRows.length?timeRows.map((r,i)=>{
      const meta=[r.type,r.stop?('stop: '+r.stop):'',r.dir?('dir: '+r.dir):'',r.name?('naam: '+r.name):''].filter(Boolean).join(' \u00b7 ');
      return `<tr>
    <td><b>${esc(r.bus||'?')}</b><div class="pe" style="font-size:11px;color:var(--muted2)">${esc(r.reg||'')}${r.bus_id?' \u00b7 <span class="mono">'+esc(r.bus_id)+'</span>':''}</div></td>
    <td>${esc(r.route||'')}</td>
    <td class="mono">${esc(fmtTime(r.current||'\u2014'))} \u2192 <b style="color:var(--ok)">${esc(fmtTime(r.time||'\u2014'))}</b></td>
    <td style="max-width:220px;font-size:12px">${esc(r.note||'')}<div class="pe" style="font-size:11px;color:var(--muted2)">${esc(meta)}</div></td>
    <td class="mono" style="white-space:nowrap;font-size:11.5px">${esc(String(r.key).split('|')[0])}</td>
    <td>${canAutoRpt(r)?`<button class="btn btn-primary btn-sm" data-a="approve" data-i="${i}">Approve</button> `:''}<button class="btn btn-ghost btn-sm" data-a="fix" data-i="${i}">Fix</button> <button class="btn btn-danger btn-sm" data-a="reject" data-i="${i}">Reject</button></td></tr>`
    }).join(''):'<tr><td colspan="6" class="empty">Koi naya time update nahi \u2014 sab clear!'+(done?' ('+done+' purane done/rejected)':'')+'</td></tr>';
    tb.querySelectorAll('button[data-a]').forEach(btn=>btn.onclick=()=>rptAction(btn.dataset.a,+btn.dataset.i));
  }else{
    const tname=(r)=>r.type==='bus-stopped'?'Bus nahi chalti':(r.type==='route-change'?'Route badli':(r.type||'report'));
    tb.innerHTML=issRows.length?issRows.map((r,i)=>`<tr>
    <td><b>${esc(r.bus||'?')}</b><div class="pe" style="font-size:11px;color:var(--muted2)">${esc(r.reg||'')}${r.bus_id?' \u00b7 <span class="mono">'+esc(r.bus_id)+'</span>':''}</div></td>
    <td>${esc(r.route||'')}</td>
    <td><span class="tag o">${esc(tname(r))}</span></td>
    <td style="max-width:220px;font-size:12px">${esc(r.note||'')}<div class="pe" style="font-size:11px;color:var(--muted2)">${esc(r.name?('naam: '+r.name):'')}</div></td>
    <td class="mono" style="white-space:nowrap;font-size:11.5px">${esc(String(r.key).split('|')[0])}</td>
    <td>${r.bus_id?`<button class="btn btn-ghost btn-sm" data-a="fix" data-i="${i}">Fix</button> `:''}<button class="btn btn-primary btn-sm" data-a="done" data-i="${i}">Handled</button> <button class="btn btn-danger btn-sm" data-a="reject" data-i="${i}">Reject</button></td></tr>`).join(''):'<tr><td colspan="6" class="empty">Koi issue report nahi \u2014 sab clear!</td></tr>';
    tb.querySelectorAll('button[data-a]').forEach(btn=>btn.onclick=()=>issAction(btn.dataset.a,+btn.dataset.i));
  }
}''')

INS_ANCHOR = "$('#rebuildBtn')?.addEventListener"
INS_NEW = ('''/* ---------- issue reports + new bus contributions ---------- */
let ISSUES=null,BUSROWS=null;
function setBadge(id,n){const b=document.getElementById(id);if(b){b.style.display=n?'inline-flex':'none';b.textContent=n}}
function fmtTime(v){
  if(v==null||v==='')return '\u2014';
  const s=String(v).trim();
  let m=s.match(/^\\d{4}-\\d{2}-\\d{2}T(\\d{2}):(\\d{2})/);
  if(m){let h=+m[1];h=h%24;const ap=h>=12?'PM':'AM';h=h%12||12;return h+':'+m[2]+' '+ap}
  m=s.match(/^(\\d{1,2}):(\\d{2})(?::\\d{2})?$/);
  if(m){let h=+m[1];h=((h%24)+24)%24;const ap=h>=12?'PM':'AM';h=h%12||12;return h+':'+m[2]+' '+ap}
  return s;
}
async function issAction(a,i){
  const r=ISSUES&&ISSUES[i];if(!r)return;
  if(a==='fix'){go('buses');openBus(r.bus_id);return}
  if(a==='reject'){
    if(!await confirmBox('Reject?','<b>'+esc(r.bus||'?')+'</b> issue reject karein?'))return;
    await rptAct('reject',r.key);toast('\u2713 Rejected','ok');loadReports('issues');return;
  }
  if(!await confirmBox('Handled mark karein?','<b>'+esc(r.bus||'?')+'</b> \u2014 ye issue dekh liya? Sheet mein approved mark ho jayega.'))return;
  await rptAct('approve',r.key);toast('\u2713 Marked handled','ok');loadReports('issues');
}
async function findDup(r){
  try{await ensureIdx()}catch(e){}
  let cb={add:[]};
  try{cb=JSON.parse(await rawGet('data/community_buses.json'))}catch(e){}
  const nreg=String(r.reg||'').replace(/\\s+/g,'').toUpperCase();
  const nb=String(r.bus||'').toLowerCase().replace(/[^a-z0-9]/g,'');
  const ofrom=String(r.from||'').toLowerCase().trim(),oto=String(r.to||'').toLowerCase().trim();
  const all=[];
  if(IDX&&IDX.buses)for(const b of IDX.buses)all.push([b.bus_name||'',b.reg_no||'',b.origin||'',b.destination||'']);
  if(cb.add)for(const b of cb.add)all.push([b.bus_name||'',b.reg_no||'',b.origin||'',b.destination||'']);
  for(const b of all){
    const breg=String(b[1]).replace(/\\s+/g,'').toUpperCase();
    if(nreg&&breg&&nreg===breg)return{bus_name:b[0],reg_no:b[1],origin:b[2],destination:b[3]};
    const bb=String(b[0]).toLowerCase().replace(/[^a-z0-9]/g,'');
    if(nb&&bb&&nb===bb&&String(b[2]).toLowerCase().trim()===ofrom&&String(b[3]).toLowerCase().trim()===oto)return{bus_name:b[0],reg_no:b[1],origin:b[2],destination:b[3]};
  }
  return null;
}
function parseStops(r){
  const out=[];
  const parts=String(r.stops||'').split(';').map(x=>x.trim()).filter(Boolean);
  for(const p of parts){
    const m=p.match(/^(.+?)\\s*@\\s*(.+)$/);
    if(m)out.push({name:m[1].trim(),up:m[2].trim(),down:''});
    else out.push({name:p,up:'',down:''});
  }
  if(!out.length){
    out.push({name:r.from||'',up:fmtTime(r.dep)==='\u2014'?'':fmtTime(r.dep),down:''});
    out.push({name:r.to||'',up:'',down:''});
  }
  return out;
}
async function loadNewBuses(){
  const tb=$('#busRows');
  const tk=rptTok();
  if(!tk){tb.innerHTML='<tr><td colspan="7" class="empty">Pehle Settings mein <b>Report Receiver Token</b> daalo.</td></tr>';return}
  tb.innerHTML='<tr><td colspan="7" class="empty">Loading\u2026</td></tr>';
  let rows=[];
  try{
    const r=await fetch(RPT_URL+'?action=list-buses&token='+encodeURIComponent(tk));
    const j=await r.json();
    rows=(j.rows||[]).filter(x=>x.status==='new'||x.status==='invalid');
  }catch(e){tb.innerHTML='<tr><td colspan="7" class="empty">Load fail: '+esc(e.message)+'</td></tr>';return}
  BUSROWS=rows;
  const fresh=rows.filter(x=>x.status==='new');
  setBadge('busBadge',fresh.length);
  const st=$('#stBusesNew');if(st)st.textContent=fresh.length;
  if(!rows.length){tb.innerHTML='<tr><td colspan="7" class="empty">Koi nayi bus submission nahi \u2014 sab clear!</td></tr>';return}
  tb.innerHTML=rows.map((r,i)=>{
    const inv=r.status==='invalid';
    const stopNames=String(r.stops||'').split(';').map(x=>x.trim().split('@')[0].trim()).filter(Boolean).join(', ');
    return `<tr style="${inv?'opacity:.55':''}">
    <td><b>${esc(r.bus||'?')}</b>${inv?' <span class="tag o">invalid</span>':''}<div class="pe" style="font-size:11px;color:var(--muted2)">${esc(r.reg||'\u2014')}</div><div id="dup${i}" style="font-size:11px;color:#b8791f;font-weight:600"></div></td>
    <td>${esc(r.from||'?')} \u2192 ${esc(r.to||'?')}</td>
    <td class="mono" style="white-space:nowrap">${esc(fmtTime(r.dep))}${r.arr?' \u2013 '+esc(fmtTime(r.arr)):''}</td>
    <td style="max-width:180px;font-size:12px">${esc(stopNames||'\u2014')}</td>
    <td style="font-size:12px">${esc(r.name||'')}${r.email?'<div class="pe" style="font-size:11px;color:var(--muted2)">'+esc(r.email)+'</div>':''}${r.contact?'<div class="pe" style="font-size:11px;color:var(--muted2)">'+esc(r.contact)+'</div>':''}</td>
    <td class="mono" style="white-space:nowrap;font-size:11.5px">${esc(String(r.key).split('|')[0])}</td>
    <td>${inv?`<button class="btn btn-danger btn-sm" data-a="reject" data-i="${i}">Delete</button>`:`<button class="btn btn-primary btn-sm" data-a="approve" data-i="${i}">Approve</button> <button class="btn btn-danger btn-sm" data-a="reject" data-i="${i}">Reject</button>`}</td></tr>`;
  }).join('');
  tb.querySelectorAll('button[data-a]').forEach(btn=>btn.onclick=()=>busAction(btn.dataset.a,+btn.dataset.i));
  rows.forEach(async (r,i)=>{
    if(r.status!=='new')return;
    try{
      const d=await findDup(r);
      if(d){const c=document.getElementById('dup'+i);if(c)c.innerHTML='\u26a0 Duplicate mila: '+esc(d.bus_name||'')+' '+(d.reg_no?'('+esc(d.reg_no)+') ':'')+(d.origin?esc(d.origin)+'\u2192'+esc(d.destination):'')}
    }catch(e){}
  });
}
async function busAction(a,i){
  const r=BUSROWS&&BUSROWS[i];if(!r)return;
  if(a==='reject'){
    if(!await confirmBox('Reject?','<b>'+esc(r.bus||'?')+'</b> submission reject karein?'))return;
    await rptAct('reject-bus',r.key);toast('\u2713 Rejected','ok');loadNewBuses();return;
  }
  const dup=await findDup(r).catch(()=>null);
  if(dup&&!await confirmBox('Duplicate lag raha hai!','Ye bus shayad pehle se site pe hai ('+esc(dup.bus_name||'')+'). Phir bhi add karein?'))return;
  if(!await confirmBox('Approve & site pe add?','<b>'+esc(r.bus||'?')+'</b> ('+esc(r.from||'?')+' \u2192 '+esc(r.to||'?')+') \u2014 community_buses.json update hoga + rebuild chalega (3-5 min live).'))return;
  try{
    let sha=null,cb={add:[],enrich:[]};
    try{const cr=await gh('/repos/'+S.repo+'/contents/data/community_buses.json');sha=cr.sha;cb=JSON.parse(b64d(cr.content))}catch(e){}
    if(!cb.add)cb.add=[];
    if(!cb.enrich)cb.enrich=[];
    cb.add.push({
      operator:r.bus||'Community',
      bus_name:r.bus||'',
      bus_type:'Private - Non AC',
      reg_no:r.reg||'',
      origin:r.from||'',
      destination:r.to||'',
      departure_time:fmtTime(r.dep)==='\u2014'?'':fmtTime(r.dep),
      arrival_time:fmtTime(r.arr)==='\u2014'?'':fmtTime(r.arr),
      route:(r.from||'')+' - '+(r.to||''),
      source:'community contribution (form)',
      detail_url:'',
      contact_number:r.contact||'',
      stops:parseStops(r)
    });
    await ghPut('data/community_buses.json',JSON.stringify(cb,null,2)+'\\n','New bus approved: '+(r.bus||'')+' '+(r.from||'')+'-'+(r.to||'')+(r.name?(' (by '+r.name+')'):''),sha);
    try{await gh('/repos/'+S.repo+'/actions/workflows/apply-overrides.yml/dispatches',{method:'POST',body:JSON.stringify({ref:'main'})})}catch(e){}
    await rptAct('approve-bus',r.key);
    if(r.name){
      let csha=null,list=[];
      try{const cr=await gh('/repos/'+S.repo+'/contents/data/contributors.json');csha=cr.sha;list=JSON.parse(b64d(cr.content))}catch(e){}
      const f=list.find(c=>(c.name||'').toLowerCase()===String(r.name).toLowerCase());
      if(f)f.count=(f.count||1)+1;else list.push({name:r.name,count:1});
      list.sort((x,y)=>(y.count||0)-(x.count||0));
      await ghPut('data/contributors.json',JSON.stringify(list.slice(0,20),null,2)+'\\n','contributors \u2014 '+r.name,csha);
    }
    toast('\u2713 Approved \u2014 rebuild chal pada, 3-5 min mein live','ok');
    loadNewBuses();
  }catch(e){toast('\u2717 Fail: '+e.message,'err')}
}

$('#rebuildBtn')?.addEventListener''')

def main():
    s = io.open('admin.html', encoding='utf-8').read()
    if 'view-newbuses' in s:
        print('admin.html: already patched')
    else:
        s = rep(s, NAV_OLD, NAV_NEW, 'nav items')
        s = rep(s, STAT_OLD, STAT_NEW, 'dashboard stats')
        s = rep(s, QA_OLD, QA_NEW, 'quick actions')
        s = rep(s, SEC_OLD, SEC_NEW, 'view sections')
        s = rep(s, GO_T_OLD, GO_T_NEW, 'go titles')
        s = rep(s, GO_C_OLD, GO_C_NEW, 'go crumbs')
        s = rep(s, GO_L_OLD, GO_L_NEW, 'go loads')
        s = rep(s, DASH_OLD, DASH_NEW, 'loadDash counts')
        i = s.find(LR_START)
        assert i > 0, 'loadReports start not found'
        j = s.find(LR_END, i)
        assert j > 0, 'loadReports end not found'
        s = s[:i] + LR_NEW + s[j + len(LR_END):]
        k = s.find(INS_ANCHOR)
        assert k > 0, 'rebuild anchor not found'
        s = s[:k] + INS_NEW + s[k + len(INS_ANCHOR):]
        io.open('admin.html', 'w', encoding='utf-8').write(s)
        print('admin.html: 3 sections + new buses admin + dup detection + AM/PM done')

    y = io.open('.github/workflows/apply-overrides.yml', encoding='utf-8').read()
    if 'add_community_buses' in y:
        print('apply-overrides.yml: already patched')
    else:
        old = "      - name: Merge admin time overrides into source data\n        run: python3 scripts/apply_time_overrides.py\n"
        new = ("      - name: Merge community bus contributions\n"
               "        run: python3 scripts/add_community_buses.py --write\n\n"
               "      - name: Merge admin time overrides into source data\n"
               "        run: python3 scripts/apply_time_overrides.py\n")
        s2 = rep(y, old, new, 'overrides workflow community step')
        io.open('.github/workflows/apply-overrides.yml', 'w', encoding='utf-8').write(s2)
        print('apply-overrides.yml: community merge step added')

if __name__ == '__main__':
    main()
