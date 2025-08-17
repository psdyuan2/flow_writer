document.addEventListener('DOMContentLoaded', () => {
    // --- 全局状态管理 ---
    const state = { projects: [], currentProjectId: null, isSidebarOpen: false, currentProjectData: null, currentlyEditing: { type: null, id: null } };
    const API_BASE_URL = 'http://127.0.0.1:8000';
    let loadingInterval = null;

    // --- DOM 元素获取 ---
    const sidebar = document.getElementById('projects-sidebar'), appWrapper = document.getElementById('app-wrapper'), toggleSidebarBtn = document.getElementById('toggle-sidebar-button'), projectsList = document.getElementById('projects-list'), newProjectBtn = document.getElementById('new-project-button'), currentProjectTitle = document.getElementById('current-project-title'), startView = document.getElementById('start-view'), startIdeaInput = document.getElementById('start-idea-input'), startCreationButton = document.getElementById('start-creation-button'), modal = document.getElementById('new-project-modal'), ideaInputInModal = document.getElementById('idea-input'), createProjectBtnInModal = document.getElementById('create-project-button'), cancelCreateBtn = document.getElementById('cancel-create-button'), outlinePanel = document.getElementById('outline-panel'), editorActions = document.getElementById('editor-actions'), loader = document.getElementById('loader'), loaderText = document.getElementById('loader-text'), textEditor = document.getElementById('text-editor'), characterEditor = document.getElementById('character-editor'), genericTitle = textEditor.querySelector('.editor-title'), genericContent = textEditor.querySelector('.editor-content'), charTitle = characterEditor.querySelector('.editor-title');
    const charInputs = { name: document.getElementById('char-name'), role: document.getElementById('char-role'), description: document.getElementById('char-description') };
    const saveButton = document.getElementById('save-button'), generateChapterButton = document.getElementById('generate-chapter-button'), deleteCharacterButton = document.getElementById('delete-character-button'), characterList = document.getElementById('character-list'), addCharacterButton = document.getElementById('add-character-button');

    // --- API 调用封装 ---
    async function apiCall(endpoint, method = 'GET', body = null) { toggleLoading(true); try { const options = { method, headers: { 'Content-Type': 'application/json' } }; if (body) options.body = JSON.stringify(body); const response = await fetch(`${API_BASE_URL}${endpoint}`, options); if (!response.ok) { const errorData = await response.json(); throw new Error(errorData.detail || `API request failed with status ${response.status}`); } if (response.status === 204) return null; const responseText = await response.text(); return responseText ? JSON.parse(responseText) : null; } catch (error) { alert(`发生错误: ${error.message}`); console.error('API Error:', error); return null; } finally { toggleLoading(false); } }

    // --- UI 更新函数 ---
    function toggleLoading(show) { loader.classList.toggle('hidden', !show); if (show) { if (typeof loadingTips !== 'undefined' && loadingTips.length > 0) { let tipIndex = Math.floor(Math.random() * loadingTips.length); loaderText.textContent = loadingTips[tipIndex]; loadingInterval = setInterval(() => { tipIndex = (tipIndex + 1) % loadingTips.length; loaderText.textContent = loadingTips[tipIndex]; }, 2500); } else { loaderText.textContent = "AI正在奋笔疾书中..."; } } else { if (loadingInterval) { clearInterval(loadingInterval); loadingInterval = null; } } }
    function toggleSidebar() { state.isSidebarOpen = !state.isSidebarOpen; sidebar.classList.toggle('open', state.isSidebarOpen); appWrapper.classList.toggle('sidebar-open', state.isSidebarOpen); }
    function renderProjectsList() { projectsList.innerHTML = ''; state.projects.forEach(project => { const li = document.createElement('li'); li.className = 'project-list-item'; li.dataset.projectId = project.id; li.title = project.initial_idea; li.textContent = project.initial_idea; if (project.id === state.currentProjectId) { li.classList.add('active'); } const deleteBtn = document.createElement('button'); deleteBtn.className = 'delete-project-btn'; deleteBtn.innerHTML = '&times;'; deleteBtn.title = "删除项目"; li.appendChild(deleteBtn); projectsList.appendChild(li); }); }
    function renderOutlinePanel() { if (!state.currentProjectData) return; characterList.innerHTML = ''; state.currentProjectData.characters.forEach(char => { const li = document.createElement('li'); li.className = 'outline-item'; li.dataset.type = 'character'; li.dataset.id = char.id; li.innerHTML = `${char.name} <small>${char.role}</small>`; characterList.appendChild(li); }); const chapterList = document.getElementById('chapter-list'); chapterList.innerHTML = ''; state.currentProjectData.chapters.forEach(chapter => { const li = document.createElement('li'); li.className = 'outline-item'; li.dataset.type = 'chapter'; li.dataset.id = chapter.id; li.innerHTML = `${chapter.title} <small>${chapter.status === 'completed' ? '已完成' : '仅大纲'}</small>`; chapterList.appendChild(li); }); }
    function hideAllEditors() { textEditor.classList.add('hidden'); characterEditor.classList.add('hidden'); }
    function updateActiveOutlineItem(type, id) { document.querySelectorAll('.outline-item.active').forEach(el => el.classList.remove('active')); let selector; if (['synopsis', 'style'].includes(type)) { selector = `[data-type="${type}"]`; } else { selector = `[data-type="${type}"][data-id="${id}"]`; } const activeEl = outlinePanel.querySelector(selector); if (activeEl) { activeEl.classList.add('active'); } }

    function renderEditorPanel(type, id) {
        if (!state.currentProjectData) return;
        hideAllEditors();
        startView.classList.add('hidden');
        editorActions.classList.remove('hidden');
        generateChapterButton.classList.add('hidden');
        deleteCharacterButton.classList.add('hidden');
        if (type === 'synopsis' || type === 'style') {
            textEditor.classList.remove('hidden');
            genericTitle.textContent = type === 'synopsis' ? '故事梗概' : '写作风格';
            genericContent.value = type === 'synopsis' ? state.currentProjectData.synopsis : state.currentProjectData.writing_style;
        } else if (type === 'character') {
            characterEditor.classList.remove('hidden');
            deleteCharacterButton.classList.remove('hidden');
            const char = state.currentProjectData.characters.find(c => c.id === id);
            if (!char) { console.error("BUG: renderEditorPanel中未找到ID为", id, "的角色。"); return; }
            charTitle.textContent = `编辑人物: ${char.name || '未命名'}`;
            for (const key in charInputs) {
                if (Object.hasOwnProperty.call(char, key) && Object.hasOwnProperty.call(charInputs, key)) {
                    charInputs[key].value = char[key] || '';
                }
            }
        } else if (type === 'chapter') {
            textEditor.classList.remove('hidden');
            const chapter = state.currentProjectData.chapters.find(c => c.id == id);
            if(!chapter) { console.error("BUG: 未找到ID为", id, "的章节。"); return; }
            genericTitle.textContent = `章节: ${chapter.title}`;
            chapter.status === 'completed' ? (genericContent.value = chapter.content) : (genericContent.value = chapter.outline);
            if (chapter.status !== 'completed') { generateChapterButton.classList.remove('hidden'); }
        }
        state.currentlyEditing = { type, id };
        updateActiveOutlineItem(type, id);
    }

    // --- 核心工作流函数 ---
    function showStartView() { outlinePanel.classList.add('hidden'); hideAllEditors(); editorActions.classList.add('hidden'); startView.classList.remove('hidden'); state.currentProjectId = null; state.currentProjectData = null; currentProjectTitle.textContent = 'FlowWriter'; renderProjectsList(); }
    async function initializeApp() { const projects = await apiCall('/api/projects'); if (projects) { state.projects = projects; renderProjectsList(); } showStartView(); }

    async function loadProject(projectId) {
        const projectData = await apiCall(`/api/projects/${projectId}`);
        if (!projectData) return;
        state.currentProjectId = projectId;
        state.currentProjectData = projectData;
        startView.classList.add('hidden');
        outlinePanel.classList.remove('hidden');
        currentProjectTitle.textContent = projectData.initial_idea;
        renderOutlinePanel();

        // **核心修复点**: 项目加载后，自动显示第一个角色的信息
        if (projectData.characters && projectData.characters.length > 0) {
            const firstCharacter = projectData.characters[0];
            if (firstCharacter && firstCharacter.id) {
                renderEditorPanel('character', firstCharacter.id);
            } else {
                console.error("加载项目后，第一个角色没有ID!", firstCharacter);
                hideAllEditors();
                editorActions.classList.add('hidden');
            }
        } else {
            // 如果没有角色，则隐藏所有编辑器
            hideAllEditors();
            editorActions.classList.add('hidden');
        }
        renderProjectsList();
    }

    async function createNewProject(idea) { if (!idea) return alert('请输入你的故事想法！'); const newProject = await apiCall('/api/projects', 'POST', { idea, num_chapters: 5 }); if (newProject) { state.projects.unshift({ id: newProject.id, initial_idea: newProject.initial_idea }); renderProjectsList(); await loadProject(newProject.id); } }

    // --- 事件处理函数 ---
    async function handleStartFromBlank() { await createNewProject(startIdeaInput.value.trim()); startIdeaInput.value = ''; }
    async function handleCreateFromModal() { hideNewProjectModal(); await createNewProject(ideaInputInModal.value.trim()); }
    function handleProjectsListClick(event) { const listItem = event.target.closest('.project-list-item'); if (!listItem) return; const projectId = listItem.dataset.projectId; if (event.target.classList.contains('delete-project-btn')) { event.stopPropagation(); handleDeleteProject(projectId); } else if (projectId !== state.currentProjectId) { loadProject(projectId); } }
    async function handleDeleteProject(projectId) { const project = state.projects.find(p => p.id === projectId); if (confirm(`确定要删除作品 “${project.initial_idea.substring(0, 30)}...” 吗？`)) { const result = await apiCall(`/api/projects/${projectId}`, 'DELETE'); if (result === null) { state.projects = state.projects.filter(p => p.id !== projectId); if (projectId === state.currentProjectId) { showStartView(); } else { renderProjectsList(); } } } }
    function showNewProjectModal() { modal.classList.remove('hidden'); ideaInputInModal.value = ''; ideaInputInModal.focus(); }
    function hideNewProjectModal() { modal.classList.add('hidden'); }
    function handleOutlineClick(event) { const item = event.target.closest('.outline-item'); if (!item) return; const { type, id } = item.dataset; renderEditorPanel(type, id); }
    async function handleSaveChanges() { if (!state.currentProjectData || state.currentlyEditing.type === null) return; const { type, id } = state.currentlyEditing; if (type === 'synopsis') { state.currentProjectData.synopsis = genericContent.value; } else if (type === 'style') { state.currentProjectData.writing_style = genericContent.value; } else if (type === 'character') { const char = state.currentProjectData.characters.find(c => c.id === id); if (char) { for (const key in charInputs) { if(Object.hasOwnProperty.call(charInputs, key)) char[key] = charInputs[key].value.trim(); } } } else if (type === 'chapter') { const chapter = state.currentProjectData.chapters.find(c => c.id == id); if (chapter) { chapter.status === 'completed' ? (chapter.content = genericContent.value) : (chapter.outline = genericContent.value); } } const updatedProject = await apiCall(`/api/projects/${state.currentProjectId}`, 'PUT', state.currentProjectData); if (updatedProject) { state.currentProjectData = updatedProject; alert('保存成功！'); renderOutlinePanel(); updateActiveOutlineItem(type, id); } }
    async function handleAddCharacter() { if (!state.currentProjectData) return; state.currentProjectData.characters.push({ name: "新人物", role: "配角", description: "请填写简介" }); state.currentlyEditing = { type: 'character', id: null }; const updatedProject = await apiCall(`/api/projects/${state.currentProjectId}`, 'PUT', state.currentProjectData); if (updatedProject) { state.currentProjectData = updatedProject; renderOutlinePanel(); const newlyAddedChar = updatedProject.characters[updatedProject.characters.length - 1]; if (newlyAddedChar && newlyAddedChar.id) { renderEditorPanel('character', newlyAddedChar.id); } } }
    async function handleDeleteCharacter() { if (!state.currentProjectData || state.currentlyEditing.type !== 'character') return; const charId = state.currentlyEditing.id; const char = state.currentProjectData.characters.find(c => c.id === charId); if (!char) return; if (confirm(`你确定要删除人物 “${char.name}” 吗？`)) { state.currentProjectData.characters = state.currentProjectData.characters.filter(c => c.id !== charId); const updatedProject = await apiCall(`/api/projects/${state.currentProjectId}`, 'PUT', state.currentProjectData); if (updatedProject) { state.currentProjectData = updatedProject; alert('人物已删除。'); if (updatedProject.characters.length > 0) { renderEditorPanel('character', updatedProject.characters[0].id); } else { hideAllEditors(); editorActions.classList.add('hidden'); } renderOutlinePanel(); } } }
    async function handleGenerateChapter() { if (state.currentlyEditing.type !== 'chapter') return; const chapterId = state.currentlyEditing.id; if (confirm('你确定要根据当前大纲生成本章内容吗？')) { const updatedProject = await apiCall('/api/generate-chapter', 'POST', { project_id: state.currentProjectId, chapter_id: parseInt(chapterId) }); if (updatedProject) { state.currentProjectData = updatedProject; renderOutlinePanel(); renderEditorPanel('chapter', chapterId); } } }

    // --- 事件监听器绑定 ---
    toggleSidebarBtn.addEventListener('click', toggleSidebar);
    projectsList.addEventListener('click', handleProjectsListClick);
    newProjectBtn.addEventListener('click', showNewProjectModal);
    cancelCreateBtn.addEventListener('click', hideNewProjectModal);
    createProjectBtnInModal.addEventListener('click', handleCreateFromModal);
    startCreationButton.addEventListener('click', handleStartFromBlank);
    outlinePanel.addEventListener('click', handleOutlineClick);
    saveButton.addEventListener('click', handleSaveChanges);
    addCharacterButton.addEventListener('click', handleAddCharacter);
    deleteCharacterButton.addEventListener('click', handleDeleteCharacter);
    generateChapterButton.addEventListener('click', handleGenerateChapter);

    // --- 应用启动 ---
    initializeApp();
});
