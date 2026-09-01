(() => {
  const drop = document.querySelector('#drop-zone');
  const results = document.querySelector('#results');
  const rows = document.querySelector('#file-rows');
  const findings = document.querySelector('#findings');
  const metrics = document.querySelector('#metrics');
  const decoder = new TextDecoder('latin1');
  const objectNames = {
    '1.2.840.10008.5.1.4.1.1.2':'CT','1.2.840.10008.5.1.4.1.1.4':'MR',
    '1.2.840.10008.5.1.4.1.1.481.1':'RTIMAGE','1.2.840.10008.5.1.4.1.1.481.2':'RTDOSE',
    '1.2.840.10008.5.1.4.1.1.481.3':'RTSTRUCT','1.2.840.10008.5.1.4.1.1.481.5':'RTPLAN'
  };
  const tags = {
    '0008,0016':'sop','0008,0060':'modality','0008,0080':'institution','0010,0010':'patientName',
    '0010,0020':'patientId','0010,0030':'birthDate','0020,000d':'study','0020,000e':'series','0020,0052':'frame'
  };
  const longVR = new Set(['OB','OD','OF','OL','OV','OW','SQ','UC','UR','UT','UN']);
  const clean = value => value.replace(/\0/g,'').trim();

  function parse(buffer) {
    const view = new DataView(buffer); let p = 0; const out = {};
    if (buffer.byteLength >= 132 && decoder.decode(new Uint8Array(buffer,128,4)) === 'DICM') p = 132;
    let explicit = true, little = true, steps = 0;
    while (p + 8 <= buffer.byteLength && steps++ < 20000) {
      const group = view.getUint16(p,little), element = view.getUint16(p+2,little);
      const key = group.toString(16).padStart(4,'0') + ',' + element.toString(16).padStart(4,'0');
      let len, valueStart;
      const vr = decoder.decode(new Uint8Array(buffer,p+4,2));
      if (explicit && /^[A-Z]{2}$/.test(vr)) {
        if (longVR.has(vr)) { if (p+12>buffer.byteLength) break; len=view.getUint32(p+8,little); valueStart=p+12; }
        else { len=view.getUint16(p+6,little); valueStart=p+8; }
      } else { explicit=false; len=view.getUint32(p+4,little); valueStart=p+8; }
      if (len === 0xffffffff || valueStart + len > buffer.byteLength) { p = valueStart; continue; }
      if (tags[key] && len < 4096) out[tags[key]] = clean(decoder.decode(new Uint8Array(buffer,valueStart,len)));
      if (key === '0002,0010') {
        const ts = clean(decoder.decode(new Uint8Array(buffer,valueStart,len)));
        if (ts === '1.2.840.10008.1.2') explicit=false;
        if (ts === '1.2.840.10008.1.2.2') little=false;
      }
      if (group > 0x0020 && Object.keys(out).length >= 6) break;
      p = valueStart + len;
    }
    if (!out.sop && !out.modality) throw new Error('No readable DICOM header');
    out.object = objectNames[out.sop] || out.modality || 'DICOM';
    return out;
  }

  async function inspect(fileList) {
    const files = [...fileList].filter(f => f.size > 0); if (!files.length) return;
    const parsed = await Promise.all(files.map(async file => { try { return {file, data:parse(await file.arrayBuffer())}; } catch(error) { return {file,error}; } }));
    render(parsed); results.hidden=false; results.scrollIntoView({behavior:'smooth',block:'start'});
  }

  function render(items) {
    const valid=items.filter(x=>x.data), failed=items.length-valid.length;
    const rt=valid.filter(x=>x.data.object.startsWith('RT')).length;
    const phi=valid.filter(x=>['patientName','patientId','birthDate','institution'].some(k=>x.data[k])).length;
    const frames=new Set(valid.map(x=>x.data.frame).filter(Boolean));
    document.querySelector('#result-title').textContent=`${items.length} file${items.length===1?'':'s'} inspected`;
    metrics.innerHTML=[['Readable',valid.length],['RT objects',rt],['Privacy flags',phi],['Frame UIDs',frames.size]].map(([l,n])=>`<div class="metric"><strong>${n}</strong><span>${l}</span></div>`).join('');
    const notes=[];
    notes.push(phi?['warn',`${phi} readable file(s) contain at least one direct patient or institution field. Do not treat this dataset as anonymized.`]:['ok','No populated patient name, ID, birth date, or institution field was found in the readable headers. This is not proof of anonymization.']);
    if(failed) notes.push(['warn',`${failed} file(s) could not be parsed as basic DICOM. They may be unsupported transfer syntaxes, malformed, or non-DICOM files.`]);
    if(rt && !valid.some(x=>x.data.object==='RTSTRUCT')) notes.push(['warn','RT objects were found, but no RTSTRUCT was detected in this selection.']);
    if(rt && frames.size>1) notes.push(['warn',`${frames.size} Frame of Reference UIDs were found. Confirm that cross-frame registrations or intended reference relationships exist.`]);
    if(!failed) notes.push(['ok','All selected files exposed a readable basic DICOM header.']);
    findings.innerHTML=notes.map(([c,t])=>`<p class="finding ${c}">${t}</p>`).join('');
    rows.innerHTML=items.map(({file,data,error})=>{if(error)return `<tr><td>${escapeHtml(file.name)}</td><td>—</td><td>—</td><td>—</td><td>Unreadable</td></tr>`;const fields=['patientName','patientId','birthDate','institution'].filter(k=>data[k]).length;return `<tr><td>${escapeHtml(file.webkitRelativePath||file.name)}</td><td>${escapeHtml(data.object)}</td><td>${fields?fields+' present':'none found'}</td><td>${short(data.study)} / ${short(data.series)}</td><td>Readable</td></tr>`}).join('');
  }
  const short=v=>v?escapeHtml(v.length>18?'…'+v.slice(-16):v):'—';
  const escapeHtml=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  ['dragenter','dragover'].forEach(e=>drop.addEventListener(e,x=>{x.preventDefault();drop.classList.add('dragging')}));
  ['dragleave','drop'].forEach(e=>drop.addEventListener(e,x=>{x.preventDefault();drop.classList.remove('dragging')}));
  drop.addEventListener('drop',e=>inspect(e.dataTransfer.files));
  document.querySelector('#file-input').addEventListener('change',e=>inspect(e.target.files));
  document.querySelector('#folder-input').addEventListener('change',e=>inspect(e.target.files));
  document.querySelector('#clear-button').addEventListener('click',()=>{results.hidden=true;rows.innerHTML='';document.querySelectorAll('input[type=file]').forEach(i=>i.value='');drop.scrollIntoView({behavior:'smooth'})});
})();
