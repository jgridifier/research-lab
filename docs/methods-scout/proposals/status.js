// Progressive enhancement (idea borrowed from the Nitro proposals site): refresh status chips from the live issues.
(function(){
  var els=document.querySelectorAll("[data-issue]"); if(!els.length) return;
  var MAP={"proposed":["\u25cb","New"],"approved":["\u2713","Go"],"in-progress":["\u25b6","Building"],"refine":["\u270e","Needs direction"],
           "parked":["\u275a\u275a","Parked"],"dropped":["\u2715","Dropped"],"promoted":["\u2605","Promoted"]};
  fetch("https://api.github.com/repos/jgridifier/research-lab/issues?labels=scout&state=all&per_page=100",{headers:{Accept:"application/vnd.github+json"}})
    .then(function(r){return r.ok?r.json():null}).then(function(list){
      if(!list) return; var by={};
      list.forEach(function(i){var s=null;(i.labels||[]).forEach(function(l){var n=l.name||"";if(n.indexOf("status:")===0)s=n.slice(7);});
        if(i.state==="closed"&&!s)s="dropped"; if(s&&MAP[s])by[i.number]=s;});
      els.forEach(function(el){var s=by[el.getAttribute("data-issue")]; if(!s) return;
        el.className="chip st-"+s; el.textContent=MAP[s][0]+" "+MAP[s][1];});
    }).catch(function(){});
})();
