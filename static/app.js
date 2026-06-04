
function markActiveMenu(){
  const path = window.location.pathname.replace(/\/+$/, '') || '/';
  const links = document.querySelectorAll('nav a[href]');
  let best = null;
  links.forEach(a => {
    const href = (a.getAttribute('href') || '').replace(/\/+$/, '') || '/';
    a.classList.remove('active');
    if (href === path) best = a;
    else if (href !== '/' && path.startsWith(href + '/')) {
      if (!best || href.length > (best.getAttribute('href') || '').length) best = a;
    }
  });
  if (best) best.classList.add('active');
}

function subjectSlug(name){
  return (name||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'') || 'default';
}
function subjectImage(name){
  const slug = subjectSlug(name);
  return `/static/subject_art/${slug}.svg`;
}
function updateSubjectShowcase(){
  const subject = document.getElementById('subject');
  const grade = document.getElementById('grade');
  const topic = document.getElementById('topic');
  const img = document.getElementById('subjectPreviewImg');
  const title = document.getElementById('subjectPreviewTitle');
  const desc = document.getElementById('subjectPreviewDesc');
  const meta = document.getElementById('subjectPreviewMeta');
  if(!subject || !img || !title || !desc || !meta) return;
  const subjectName = subject.options[subject.selectedIndex]?.textContent || 'Disciplina';
  const gradeName = grade?.options[grade.selectedIndex]?.textContent || 'Turma';
  const topicName = topic?.options[topic.selectedIndex]?.textContent || 'Conteúdo';
  img.src = subjectImage(subjectName);
  img.alt = `Ilustração de ${subjectName}`;
  title.textContent = subjectName;
  desc.textContent = `Conteúdo em foco: ${topicName}. O sistema adapta o material ao perfil da turma e ao estilo do professor.`;
  meta.innerHTML = `<span class="subject-badge">${gradeName}</span><span class="subject-badge">${topicName}</span>`;
}
async function setupTopics(){
  const subject=document.getElementById('subject'), grade=document.getElementById('grade'), topic=document.getElementById('topic'), help=document.getElementById('topicHelp');
  if(!subject||!grade||!topic)return;
  async function load(){
    topic.innerHTML='<option value="">Carregando...</option>';
    if(help){help.textContent='Buscando conteúdos disponíveis...';help.className='field-help';}
    updateSubjectShowcase();
    try{
      const r=await fetch(`/api/topics?subject=${encodeURIComponent(subject.value)}&grade=${encodeURIComponent(grade.value)}`, {headers:{'Accept':'application/json'}});
      if(!r.ok) throw new Error('HTTP '+r.status);
      const raw=await r.json();
      const data=Array.isArray(raw) ? raw : (raw.topicos || []);
      topic.innerHTML='';
      if(!data.length){
        topic.innerHTML='<option value="">Nenhum conteúdo cadastrado</option>';
        if(help){help.textContent='Ainda não há conteúdos para essa combinação. Escolha outra turma/matéria ou complete o banco no admin.';help.className='field-help warn';}
        updateSubjectShowcase();
        return;
      }
      data.forEach(t=>{const o=document.createElement('option');o.value=t.id;o.textContent=t.name;topic.appendChild(o);});
      if(help){help.textContent=`${data.length} conteúdo(s) encontrado(s).`;help.className='field-help ok';}
      updateSubjectShowcase();
    }catch(e){
      topic.innerHTML='<option value="">Erro ao carregar</option>';
      if(help){help.textContent='Erro ao carregar conteúdos. Atualize a página ou faça login novamente.';help.className='field-help warn';}
      console.error(e);
      updateSubjectShowcase();
    }
  }
  subject.addEventListener('change',load);
  grade.addEventListener('change',load);
  topic.addEventListener('change',updateSubjectShowcase);
  load();
}
window.addEventListener('load',()=>{
  markActiveMenu();
  preventDoubleSubmit();
  if(document.getElementById('subject')) setupTopics();
  updateSubjectShowcase();
});


function preventDoubleSubmit(){
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', () => {
      const btn = form.querySelector('button[type="submit"], button:not([type])');
      if(btn){
        btn.disabled = true;
        btn.dataset.oldText = btn.textContent;
        btn.textContent = 'Gerando...';
        setTimeout(() => { btn.disabled = false; btn.textContent = btn.dataset.oldText || 'Gerar'; }, 8000);
      }
    });
  });
}


function v25FinalForms(){
  document.querySelectorAll('form').forEach(form=>{
    form.addEventListener('submit',()=>{
      const btn=form.querySelector('button[type="submit"], button:not([type])');
      if(btn && !btn.dataset.loading){
        btn.dataset.loading='1';
        btn.dataset.oldText=btn.textContent;
        btn.textContent='Processando...';
      }
    });
  });
}
window.addEventListener('load', v25FinalForms);
