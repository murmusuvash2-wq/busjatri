#!/usr/bin/env python3
"""Upgrade admin.html Reports section: fetch reports directly from the Apps
Script receiver (Google Sheet), with real Approve / Reject / Fix buttons.
Approve writes the time override + contributor credit to GitHub (goes live on
site) and marks the Sheet row approved. Adds a Report Receiver Token field in
Settings (localStorage only — token never stored in this public repo)."""
import io

NEW_BLOCK = r"""/* ---------- user reports (Google Sheet via Apps Script) ---------- */
const RPT_URL='https://script.google.com/macros/s/AKfycbyf-rjtn606T1FUfGaPiYnyIMCZIU99ZlwqmkI3cVfPT0SarjTY12MZQpu2exLczdUD/exec';
let REPORTS=null;
function rptTok(){try{return localStorage.getItem('bj_rpt_token')||''}catch(e){return ''}}
function canAutoRpt(r){return r&&r.type==='add-time'&&r.bus_id&&r.stop&&/^\d{1,2}:\d{2}\s*(AM|PM)$/i.test(r.time||'')}
async function rptAct(action,key){
  const body=new URLSearchParams({action:action,key:key,token:rptTok()});
  try{
    const r=await fetch(RPT_URL,{method:'POST',body:body});
    try{const j=await r.json();return !!j.ok}catch(_){return true}
  }catch(e){
    try{fetch(RPT_URL,{method:'POST',mode:'no-cors',body:body})}catch(_){}
    return true;
  }
}
async function loadReports(){
  const tb=$('#reportRows');
  const tk=rptTok();
  if(!tk){tb.innerHTML='<tr><td colspan="6" class="empty">Pehle Settings mein <b>Report Receiver Token</b> daalo (bj-adm- wala), phir yahan wapas aao.</td></tr>';const bb=$('#repBadge');if(bb)bb.style.display='none';return}
  tb.innerHTML='<tr><td colspan="6" class="empty">Loading…</td></tr>';
  let rows=[];
  try{
    const r=await fetch(RPT_URL+'?action=list&token='+encodeURIComponent(tk));
    const j=await r.json();
    rows=j.rows||[];
  }catch(e){tb.innerHTML='<tr><td colspan="6" class="empty">Load fail: '+esc(e.message)+' — thodi der baad phir kholo</td></tr>';return}
  REPORTS=rows.filter(x=>x.status==='new');
  const done=rows.length-REPORTS.length;
  const pend=REPORTS.length;
  const bb=$('#repBadge');if(bb){bb.style.display=pend?'inline-flex':'none';bb.textContent=pend}
  const st=$('#stReports');if(st)st.textContent=pend;
  tb.innerHTML=pend?REPORTS.map((r,i)=>{
    const meta=[r.type,r.stop?('stop: '+r.stop):'',r.dir?('dir: '+r.dir):'',r.name?('naam: '+r.name):''].filter(Boolean).join(' · ');
    return `<tr>
    <td><b>${esc(r.bus||'?')}</b><div class="pe" style="font-size:11px;color:var(--muted2)">${esc(r.reg||'')}${r.bus_id?' · <span class="mono">'+esc(r.bus_id)+'</span>':''}</div></td>
    <td>${esc(r.route||'')}</td>
    <td class="mono">${esc(r.current||'—')} → <b style="color:var(--ok)">${esc(r.time||'—')}</b></td>
    <td style="max-width:220px;font-size:12px">${esc(r.note||'')}<div class="pe" style="font-size:11px;color:var(--muted2)">${esc(meta)}</div></td>
    <td class="mono" style="white-space:nowrap;font-size:11.5px">${esc(String(r.key).split('|')[0])}</td>
    <td>${canAutoRpt(r)?`<button class="btn btn-primary btn-sm" data-a="approve" data-i="${i}">Approve</button> `:''}<button class="btn btn-ghost btn-sm" data-a="fix" data-i="${i}">Fix</button> <button class="btn btn-danger btn-sm" data-a="reject" data-i="${i}">Reject</button></td></tr>`
  }).join(''):'<tr><td colspan="6" class="empty">Koi nayi report nahi — sab clear!'+(done?' ('+done+' purane done/rejected)':'')+'</td></tr>';
  tb.querySelectorAll('button[data-a]').forEach(btn=>btn.onclick=()=>rptAction(btn.dataset.a,+btn.dataset.i));
}
async function rptAction(a,i){
  const r=REPORTS[i];if(!r)return;
  if(a==='fix'){
    if(r.bus_id){go('buses');openBus(r.bus_id)}else toast('Is report mein bus ID nahi — Bus Times se search karo','err');
    return;
  }
  if(a==='reject'){
    if(!await confirmBox('Reject?','<b>'+esc(r.bus||'?')+'</b> report reject karein? (Sheet mein rejected mark hoga)'))return;
    await rptAct('reject',r.key);
    toast('✓ Rejected','ok');loadReports();return;
  }
  if(!canAutoRpt(r)){toast('Is report mein stop ya time poora nahi — Fix se manually karo','err');return}
  if(!await confirmBox('Approve & live karein?','<b>'+esc(r.bus||'?')+'</b> — stop <b>'+esc(r.stop)+'</b> ka time <b>'+esc(r.time)+'</b> site pe live ho jayega (2-3 min).'))return;
  const dir=(r.dir==='down')?'down':'up';
  try{
    let sha=null,ovr={};
    try{const rr=await gh('/repos/'+S.repo+'/contents/data/time-overrides.json');sha=rr.sha;ovr=JSON.parse(b64d(rr.content))}catch(e){}
    if(!ovr[r.bus_id])ovr[r.bus_id]={};
    const cur=ovr[r.bus_id][r.stop]||{};
    cur[dir]=r.time;
    ovr[r.bus_id][r.stop]=cur;
    const msg='Report approved: '+r.bus+' '+(r.reg||'')+' — '+r.stop+' '+dir+' '+r.time+(r.name?(' (by '+r.name+')'):'');
    await ghPut('data/time-overrides.json',JSON.stringify(ovr,null,2)+'\n',msg,sha);
    OVR=ovr;
    if(r.name){
      let csha=null,list=[];
      try{const cr=await gh('/repos/'+S.repo+'/contents/data/contributors.json');csha=cr.sha;list=JSON.parse(b64d(cr.content))}catch(e){}
      const f=list.find(c=>(c.name||'').toLowerCase()===String(r.name).toLowerCase());
      if(f)f.count=(f.count||1)+1;else list.push({name:r.name,count:1});
      list.sort((x,y)=>(y.count||0)-(x.count||0));
      await ghPut('data/contributors.json',JSON.stringify(list.slice(0,20),null,2)+'\n','contributors — '+r.name,csha);
    }
    await rptAct('approve',r.key);
    toast('✓ Approved — site pe 2-3 min mein live','ok');
    loadReports();
  }catch(e){toast('✗ Fail: '+e.message,'err')}
}

"""

def main():
    h = io.open('admin.html', encoding='utf-8').read()
    changed = False

    if 'rptAction' in h:
        print('admin.html: reports upgrade already applied')
    else:
        start = h.index('/* ---------- user reports ---------- */')
        end = h.index("$('#rebuildBtn')")
        h = h[:start] + NEW_BLOCK + h[end:]

        a_set = '<input id="setTok" type="password" placeholder="naya token paste karke Update dabayein"></div>'
        assert h.count(a_set) == 1, 'setTok anchor: %d' % h.count(a_set)
        h = h.replace(a_set, a_set + '\n          <div class="field"><label>Report Receiver Token (Sheet se reports ke liye)</label><input id="setRtok" type="password" placeholder="bj-adm- wala token paste karo"></div>')

        a_save = "  if(repo){localStorage.setItem(LS.repo,repo)}"
        assert h.count(a_save) == 1, 'saveSettings anchor: %d' % h.count(a_save)
        h = h.replace(a_save, a_save + "\n  const rt=$('#setRtok').value.trim();\n  if(rt){localStorage.setItem('bj_rpt_token',rt)}")

        a_hint = 'Users jo bus pages pe "Report wrong time" se correction bhejte hain wo yahan aate hain. Verify karo → <b>Fix</b> karke override save karo → phir <b>✓ Done</b>.'
        assert h.count(a_hint) == 1, 'hint anchor: %d' % h.count(a_hint)
        h = h.replace(a_hint, 'Site se aaye reports yahan dikhte hain (Google Sheet se). <b>Approve</b> = time site pe live. <b>Fix</b> = khud edit karke save. <b>Reject</b> = nikaal do.')

        io.open('admin.html', 'w', encoding='utf-8').write(h)
        changed = True
        print('admin.html: reports panel upgraded (Approve/Reject/Fix + token field)')

    if not changed and 'rptAction' not in h:
        raise SystemExit('unexpected state')

if __name__ == '__main__':
    main()
