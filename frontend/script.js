// script.js

document.addEventListener('DOMContentLoaded', () => {
    // --- 全局变量和状态 ---
    const API_BASE_URL = 'http://127.0.0.1:8000';
    let currentProject = null;
    let currentlyEditing = { type: null, id: null };

    // --- DOM 元素获取 ---
    const startView = document.getElementById('start-view');
    const mainView = document.getElementById('main-view');
    const loader = document.getElementById('loader');
    const ideaInput = document.getElementById('idea-input');
    const startButton = document.getElementById('start-button');

    const projectTitle = document.getElementById('project-title');
    const characterList = document.getElementById('character-list');
    const synopsisItem = document.getElementById('synopsis-item');
    const chapterList = document.getElementById('chapter-list');

    const editorWelcome = document.getElementById('editor-welcome');
    const editorWrapper = document.getElementById('editor-content-wrapper');
    const editorTitle = document.getElementById('editor-title');
    const editorContent = document.getElementById('editor-content');
    const saveButton = document.getElementById('save-button');
    const generateChapterButton = document.getElementById('generate-chapter-button');

    // --- API 调用封装 ---
    async function apiCall(endpoint, method = 'GET', body = null) {
        toggleLoading(true);
        try {
            const options = {
                method,
                headers: { 'Content-Type': 'application/json' },
            };
            if (body) {
                options.body = JSON.stringify(body);
            }
            const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'API request failed');
            }
            return await response.json();
        } catch (error) {
            alert(`发生错误: ${error.message}`);
            console.error('API Error:', error);
            return null;
        } finally {
            toggleLoading(false);
        }
    }

    // --- 渲染函数 ---
    function renderOutlinePanel() {
        if (!currentProject) return;

        projectTitle.textContent = currentProject.initial_idea.substring(0, 20) + '...';

        // 渲染人物
        characterList.innerHTML = '';
        currentProject.characters.forEach((char, index) => {
            const li = document.createElement('li');
            li.className = 'outline-item';
            li.dataset.type = 'character';
            li.dataset.id = index;
            li.innerHTML = `${char.name} <small>${char.role}</small>`;
            characterList.appendChild(li);
        });

        // 渲染章节
        chapterList.innerHTML = '';
        currentProject.chapters.forEach(chapter => {
            const li = document.createElement('li');
            li.className = 'outline-item';
            li.dataset.type = 'chapter';
            li.dataset.id = chapter.id;
            li.innerHTML = `${chapter.title} <small>${chapter.status === 'completed' ? '已完成' : '仅大纲'}</small>`;
            chapterList.appendChild(li);
        });
    }

    function renderEditorPanel(type, id) {
        if (!currentProject) return;

        editorWelcome.classList.add('hidden');
        editorWrapper.classList.remove('hidden');

        let title = '';
        let content = '';
        let isOutline = false;

        if (type === 'synopsis') {
            title = '故事梗概';
            content = currentProject.synopsis;
        } else if (type === 'character') {
            const char = currentProject.characters[id];
            title = `人物: ${char.name}`;
            content = `角色: ${char.role}\n\n描述: ${char.description}`;
        } else if (type === 'chapter') {
            const chapter = currentProject.chapters.find(c => c.id == id);
            title = `章节: ${chapter.title}`;
            if (chapter.status === 'completed') {
                content = chapter.content;
            } else {
                content = chapter.outline;
                isOutline = true;
            }
        }

        editorTitle.textContent = title;
        editorContent.value = content;
        generateChapterButton.classList.toggle('hidden', !isOutline);

        currentlyEditing = { type, id };
        updateActiveOutlineItem(type, id);
    }

    function updateActiveOutlineItem(type, id) {
        document.querySelectorAll('.outline-item.active').forEach(el => el.classList.remove('active'));
        let selector;
        if (type === 'synopsis') {
            selector = `[data-type="synopsis"]`;
        } else {
            selector = `[data-type="${type}"][data-id="${id}"]`;
        }
        const activeEl = document.querySelector(selector);
        if (activeEl) {
            activeEl.classList.add('active');
        }
    }

    function toggleLoading(show) {
        loader.classList.toggle('hidden', !show);
    }

    // --- 事件处理函数 ---
    async function handleStartProject() {
        const idea = ideaInput.value.trim();
        if (!idea) {
            alert('请输入你的故事想法！');
            return;
        }
        const projectData = await apiCall('/api/projects', 'POST', { idea: idea, num_chapters: 5 });
        if (projectData) {
            currentProject = projectData;
            startView.classList.add('hidden');
            mainView.classList.remove('hidden');
            renderOutlinePanel();
        }
    }

    function handleOutlineClick(event) {
        const item = event.target.closest('.outline-item');
        if (!item) return;

        const { type, id } = item.dataset;
        renderEditorPanel(type, id);
    }

    async function handleSaveChanges() {
        if (!currentProject || currentlyEditing.type === null) return;

        const { type, id } = currentlyEditing;
        const newContent = editorContent.value;

        if (type === 'synopsis') {
            currentProject.synopsis = newContent;
        } else if (type === 'character') {
            // 简单的解析，实际项目中可能需要更复杂的表单
            const lines = newContent.split('\n');
            currentProject.characters[id].role = lines[0].replace('角色: ','').trim();
            currentProject.characters[id].description = lines.slice(2).join('\n').replace('描述: ','').trim();
        } else if (type === 'chapter') {
            const chapter = currentProject.chapters.find(c => c.id == id);
            if (chapter.status === 'completed') {
                chapter.content = newContent;
            } else {
                chapter.outline = newContent;
            }
        }

        const updatedProject = await apiCall(`/api/projects/${currentProject.id}`, 'PUT', currentProject);
        if (updatedProject) {
            currentProject = updatedProject;
            alert('保存成功！');
            renderOutlinePanel(); // 刷新左侧面板以防状态更新
        }
    }

    async function handleGenerateChapter() {
        if (currentlyEditing.type !== 'chapter') return;

        const chapterId = currentlyEditing.id;
        const confirmGenerate = confirm('你确定要根据当前大纲生成本章内容吗？这会消耗AI额度。');
        if (!confirmGenerate) return;

        const updatedProject = await apiCall('/api/generate-chapter', 'POST', {
            project_id: currentProject.id,
            chapter_id: parseInt(chapterId)
        });

        if (updatedProject) {
            currentProject = updatedProject;
            renderOutlinePanel();
            renderEditorPanel('chapter', chapterId); // 重新渲染编辑器以显示完整内容
        }
    }

    // --- 事件监听器绑定 ---
    startButton.addEventListener('click', handleStartProject);
    document.getElementById('outline-panel').addEventListener('click', handleOutlineClick);
    saveButton.addEventListener('click', handleSaveChanges);
    generateChapterButton.addEventListener('click', handleGenerateChapter);

});
