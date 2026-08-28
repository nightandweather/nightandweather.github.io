(() => {
  const events = window.OPPORTUNITIES;
  let cursor = new Date(2026, 7, 1);
  let filter = "all";
  const grid = document.querySelector("#calendar-grid");
  const title = document.querySelector("#month-title");
  const list = document.querySelector("#event-list");
  const iso = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
  const visible = e => filter === "all" || e.type === filter;
  const hits = day => events.filter(e => visible(e) && day >= e.start && day <= (e.end || e.start));
  function renderCalendar(){
    const y=cursor.getFullYear(),m=cursor.getMonth(); title.textContent=cursor.toLocaleDateString("en-US",{month:"long",year:"numeric"}); grid.innerHTML="";
    const offset=(new Date(y,m,1).getDay()+6)%7; const days=new Date(y,m+1,0).getDate();
    for(let i=0;i<offset;i++){const blank=document.createElement("div");blank.className="day blank";grid.append(blank)}
    for(let n=1;n<=days;n++){const date=iso(new Date(y,m,n));const cell=document.createElement("div");cell.className="day";cell.innerHTML=`<span class="day-num">${n}</span>`;hits(date).forEach(e=>{const a=document.createElement("a");a.href=e.url;a.className=`cal-event ${e.type}`;a.textContent=e.title;a.title=e.note;cell.append(a)});grid.append(cell)}
  }
  function renderList(){list.innerHTML="";events.filter(visible).sort((a,b)=>a.start.localeCompare(b.start)).forEach(e=>{const a=document.createElement("a");a.className="event-row";a.href=e.url;a.innerHTML=`<time>${e.start}${e.end?` — ${e.end}`:""}</time><span><small>${e.type} · ${e.status}</small><strong>${e.title}</strong><p>${e.note}</p></span><b>Official source ↗</b>`;list.append(a)})}
  document.querySelector("#prev-month").onclick=()=>{cursor=new Date(cursor.getFullYear(),cursor.getMonth()-1,1);renderCalendar()};
  document.querySelector("#next-month").onclick=()=>{cursor=new Date(cursor.getFullYear(),cursor.getMonth()+1,1);renderCalendar()};
  document.querySelectorAll("[data-filter]").forEach(b=>b.onclick=()=>{document.querySelectorAll("[data-filter]").forEach(x=>x.classList.remove("active"));b.classList.add("active");filter=b.dataset.filter;renderCalendar();renderList()});
  renderCalendar();renderList();
})();
