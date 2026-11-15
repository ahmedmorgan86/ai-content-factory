/**
 * AI Content Factory - Command Center Interactive Application
 * State management, reactive updates, API integrations, and charts.
 */

// Application State
const state = {
    currentTab: 'dashboard',
    overview: null,
    ideas: [],
    selectedIdeaId: null,
    currentProduction: null,
    analytics: null,
    settings: {},
    loading: false,
    chartInstance: null
};

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadOverview();
    loadIdeas();
    loadAnalytics();
    loadSettings();
});

// Toast Notifications
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    const bg = type === 'success' ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300' :
               type === 'error' ? 'bg-rose-500/20 border-rose-500/50 text-rose-300' :
               'bg-sky-500/20 border-sky-500/50 text-sky-300';
    const icon = type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-triangle-exclamation' : 'fa-info-circle';
    
    toast.className = `glass-panel border px-4 py-3 rounded-xl flex items-center space-x-3 space-x-reverse text-sm shadow-xl toast-animate ${bg}`;
    toast.innerHTML = `
        <i class="fa-solid ${icon} text-lg"></i>
        <span>${message}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// Navigation Tabs
function initNavigation() {
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const target = tab.dataset.tab;
            switchTab(target);
        });
    });
}

function switchTab(tabId) {
    state.currentTab = tabId;
    document.querySelectorAll('.tab-content').forEach(section => {
        section.classList.add('hidden');
    });
    const targetSection = document.getElementById(`tab-${tabId}`);
    if (targetSection) {
        targetSection.classList.remove('hidden');
    }

    document.querySelectorAll('.nav-tab').forEach(tab => {
        if (tab.dataset.tab === tabId) {
            tab.classList.add('bg-sky-500/20', 'text-sky-400', 'border-sky-500/50');
            tab.classList.remove('text-slate-400', 'border-transparent');
        } else {
            tab.classList.remove('bg-sky-500/20', 'text-sky-400', 'border-sky-500/50');
            tab.classList.add('text-slate-400', 'border-transparent');
        }
    });

    if (tabId === 'analytics') {
        renderAnalyticsChart();
    }
}

// API: Overview
async function loadOverview() {
    try {
        const res = await fetch('/api/overview');
        const data = await res.json();
        state.overview = data;
        
        // Update KPI Cards
        document.getElementById('kpi-total-ideas').textContent = data.kpis.total_ideas;
        document.getElementById('kpi-ready-packages').textContent = data.kpis.ready_packages;
        document.getElementById('kpi-total-views').textContent = data.kpis.total_views.toLocaleString();
        document.getElementById('kpi-avg-ctr').textContent = data.kpis.avg_ctr + '%';
        document.getElementById('kpi-subscribers').textContent = '+' + data.kpis.total_subscribers.toLocaleString();
        document.getElementById('kpi-watch-hours').textContent = data.kpis.total_watch_hours.toLocaleString() + ' س';
        
        // Update recent ideas in dashboard
        renderRecentIdeas(data.recent_ideas);
    } catch (err) {
        console.error('Error loading overview:', err);
    }
}

function renderRecentIdeas(recent) {
    const container = document.getElementById('recent-ideas-list');
    if (!container) return;
    if (!recent || recent.length === 0) {
        container.innerHTML = '<p class="text-slate-500 text-sm py-4 text-center">لا توجد أفكار مولدة بعد.</p>';
        return;
    }
    container.innerHTML = recent.slice(0, 5).map(i => `
        <div class="p-3 rounded-xl bg-slate-800/50 border border-slate-700/60 flex items-center justify-between hover:border-sky-500/40 transition cursor-pointer" onclick="openStudio('${i['Idea ID']}')">
            <div class="flex items-center space-x-3 space-x-reverse">
                <span class="px-2 py-0.5 rounded text-xs font-bold ${i['Video Type'] === 'Long-form' ? 'bg-indigo-500/20 text-indigo-300' : 'bg-emerald-500/20 text-emerald-300'}">
                    ${i['Video Type'] === 'Long-form' ? 'فيديو طويل' : 'شورتس'}
                </span>
                <div>
                    <h4 class="text-sm font-semibold text-slate-200 line-clamp-1">${i['Video Title']}</h4>
                    <p class="text-xs text-slate-400">الجمهور: ${i['Target Audience'] || 'الجميع'}</p>
                </div>
            </div>
            <div class="flex items-center space-x-2 space-x-reverse">
                <span class="text-xs font-bold text-amber-400"><i class="fa-solid fa-star text-[10px] ml-1"></i>${i['Priority Score'] || '9.5'}</span>
                <button class="px-2.5 py-1 text-xs rounded-lg bg-sky-500/20 text-sky-400 hover:bg-sky-500/30">
                    استعراض <i class="fa-solid fa-arrow-left text-[10px] mr-1"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// API: Ideas Bank
async function loadIdeas(filterType = 'all', searchQuery = '') {
    try {
        let url = `/api/ideas?type=${filterType}`;
        if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
        const res = await fetch(url);
        const data = await res.json();
        state.ideas = data.ideas;
        renderIdeasTable(data.ideas);
    } catch (err) {
        console.error('Error loading ideas:', err);
    }
}

function renderIdeasTable(ideas) {
    const container = document.getElementById('ideas-container');
    const countEl = document.getElementById('ideas-count-badge');
    if (countEl) countEl.textContent = `${ideas.length} فكرة`;
    if (!container) return;

    if (!ideas || ideas.length === 0) {
        container.innerHTML = '<div class="text-center py-12 text-slate-500"><i class="fa-solid fa-lightbulb text-4xl mb-3"></i><p>لم يتم العثور على أفكار تطابق البحث.</p></div>';
        return;
    }

    container.innerHTML = ideas.map((item, idx) => `
        <div class="glass-panel p-5 rounded-2xl border border-slate-700/60 hover:border-sky-500/40 transition glass-panel-hover flex flex-col justify-between">
            <div>
                <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center space-x-2 space-x-reverse">
                        <span class="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">${item['Idea ID']}</span>
                        <span class="px-2 py-0.5 rounded text-xs font-semibold ${item['Video Type'] === 'Long-form' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'}">
                            ${item['Video Type'] === 'Long-form' ? '🎥 طويل (8-12 د)' : '⚡ شورتس (60 ث)'}
                        </span>
                    </div>
                    <div class="flex items-center space-x-1 space-x-reverse bg-amber-500/10 text-amber-300 border border-amber-500/30 px-2.5 py-0.5 rounded-full text-xs font-bold">
                        <i class="fa-solid fa-star text-[10px]"></i>
                        <span>${item['Priority Score'] || '9.5'} / 10</span>
                    </div>
                </div>

                <h3 class="font-bold text-base text-slate-100 mb-2 leading-snug">${item['Video Title']}</h3>
                <p class="text-xs text-slate-400 line-clamp-2 mb-3 leading-relaxed">${item['Video Summary'] || ''}</p>

                <div class="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/80 mb-3 text-xs">
                    <span class="text-sky-400 font-bold block mb-1">🎯 الخطاف (0-3 ثوانٍ):</span>
                    <p class="text-slate-300 italic line-clamp-2">"${item['Hook'] || ''}"</p>
                </div>
            </div>

            <div>
                <div class="flex flex-wrap gap-1.5 mb-4">
                    ${(item['SEO Keywords'] || '').split(',').slice(0, 3).map(k => `
                        <span class="text-[11px] px-2 py-0.5 rounded-md bg-slate-800/90 text-slate-400 border border-slate-700/80">#${k.trim()}</span>
                    `).join('')}
                </div>

                <div class="pt-3 border-t border-slate-800 flex items-center justify-between">
                    <span class="text-xs ${item['Status'] === 'New' ? 'text-sky-400' : 'text-emerald-400'} font-semibold">
                        <i class="fa-solid fa-circle text-[8px] ml-1"></i>${item['Status'] || 'New'}
                    </span>
                    <button onclick="openStudio('${item['Idea ID']}')" class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-gradient-to-l from-sky-500 to-indigo-600 text-white hover:from-sky-400 hover:to-indigo-500 shadow-md transition flex items-center space-x-1.5 space-x-reverse">
                        <i class="fa-solid fa-wand-magic-sparkles"></i>
                        <span>إنتاج الحزمة</span>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Action: Generate 20 Ideas
async function triggerGenerateIdeas() {
    const btn = document.getElementById('btn-gen-ideas');
    if (btn) btn.disabled = true;
    showToast('جاري توليد 20 فكرة جديدة وفحص التكرار عبر الذكاء الاصطناعي...', 'info');

    try {
        const res = await fetch('/api/ideas/generate', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(`تم بنجاح توليد وحفظ ${data.saved_count} فكرة فريدة جديدة!`, 'success');
            await loadIdeas();
            await loadOverview();
        } else {
            showToast('حدث خطأ أثناء التوليد.', 'error');
        }
    } catch (err) {
        showToast(`خطأ في الاتصال: ${err.message}`, 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
}

// Action: Open Production Studio for Idea
async function openStudio(ideaId) {
    state.selectedIdeaId = ideaId;
    switchTab('studio');
    const container = document.getElementById('studio-details-container');
    container.innerHTML = `
        <div class="text-center py-16">
            <i class="fa-solid fa-circle-notch fa-spin text-4xl text-sky-400 mb-3"></i>
            <p class="text-slate-400 text-sm">جاري جلب أصول الإنتاج للفكرة (${ideaId})...</p>
        </div>
    `;

    try {
        const res = await fetch(`/api/production/${ideaId}`);
        if (!res.ok) {
            const errBody = await res.text();
            throw new Error(`خطأ (${res.status}): ${errBody || res.statusText}`);
        }
        const data = await res.json();
        state.currentProduction = data;
        renderStudioPackage(data);
    } catch (err) {
        container.innerHTML = `<div class="p-6 text-center text-rose-400">فشل في تحميل حزمة الإنتاج: ${err.message}</div>`;
    }
}

// Render Studio Package
function renderStudioPackage(data) {
    const container = document.getElementById('studio-details-container');
    if (!data.produced) {
        const idea = data.idea || {};
        container.innerHTML = `
            <div class="glass-panel p-8 rounded-2xl border border-sky-500/30 text-center max-w-xl mx-auto my-8">
                <div class="w-16 h-16 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 flex items-center justify-center mx-auto mb-4 text-2xl">
                    <i class="fa-solid fa-film"></i>
                </div>
                <h3 class="text-xl font-bold text-white mb-2">${idea['Video Title'] || 'فكرة مختارة'}</h3>
                <p class="text-slate-400 text-sm mb-6">${idea['Video Summary'] || 'هذه الفكرة جاهزة للتنفيذ التلقائي عبر الذكاء الاصطناعي.'}</p>
                <div class="flex items-center justify-center gap-3">
                    <button onclick="runProductionForSelected('${data.idea_id}')" class="px-6 py-2.5 rounded-xl bg-gradient-to-l from-sky-500 to-indigo-600 text-white font-bold text-sm shadow-lg hover:from-sky-400 hover:to-indigo-500 transition flex items-center space-x-2 space-x-reverse">
                        <i class="fa-solid fa-play"></i>
                        <span>بدء الإنتاج الكامل (سكريبت + SEO + صور + تخزين)</span>
                    </button>
                </div>
            </div>
        `;
        return;
    }

    const meta = data.metadata || {};
    const seo = data.seo || {};
    const thumbs = data.thumbnails || {};
    const scenes = data.scenes || [];
    const audio = data.audio || null;
    const video = data.video || null;
    const frames = data.scene_frames || [];

    container.innerHTML = `
        <div class="space-y-6">
            <!-- Header Card -->
            <div class="glass-panel p-6 rounded-2xl border border-sky-500/30 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <div class="flex items-center space-x-2 space-x-reverse mb-2">
                        <span class="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-sky-400 border border-slate-700 font-bold">${data.idea_id}</span>
                        <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            <i class="fa-solid fa-check-double ml-1"></i>أصول الإنتاج جاهزة
                        </span>
                        ${video ? `
                            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                <i class="fa-solid fa-clapperboard ml-1"></i>الفيديو جاهز للنشر 🚀
                            </span>
                        ` : ''}
                        <span class="text-xs text-slate-400 font-mono">${data.storage_path}</span>
                    </div>
                    <h2 class="text-xl font-bold text-white leading-tight">${meta['Video Title'] || seo['recommended_best_title']}</h2>
                </div>
                <div class="flex flex-wrap items-center gap-3">
                    <button onclick="approvePublishing('${data.idea_id}')" class="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg transition flex items-center space-x-2 space-x-reverse">
                        <i class="fa-solid fa-circle-check"></i>
                        <span>اعتماد وجدولة النشر</span>
                    </button>
                    <button onclick="runProductionForSelected('${data.idea_id}')" class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition flex items-center space-x-2 space-x-reverse">
                        <i class="fa-solid fa-rotate"></i>
                        <span>توليد الحزمة الشاملة</span>
                    </button>
                </div>
            </div>

            <!-- READY-FOR-PUBLISHING VIDEO & VOXARABIC AUDIO HERO SECTION -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Ready-to-Publish Video Player -->
                <div class="glass-panel p-6 rounded-2xl border border-indigo-500/40 relative overflow-hidden bg-gradient-to-b from-slate-900/90 to-indigo-950/20 space-y-4">
                    <div class="flex items-center justify-between pb-3 border-b border-slate-800">
                        <div class="flex items-center space-x-2 space-x-reverse text-indigo-400 font-bold">
                            <i class="fa-solid fa-circle-play text-xl"></i>
                            <span class="text-base">الفيديو النهائي الجاهز للنشر (Rendered Video)</span>
                        </div>
                        ${video ? `
                            <span class="text-[10px] font-mono font-bold bg-indigo-500/20 text-indigo-300 px-2.5 py-1 rounded-full border border-indigo-500/30">
                                ${video.is_vertical ? '9:16 Shorts / Reels' : '16:9 YouTube Long'}
                            </span>
                        ` : ''}
                    </div>

                    ${video ? `
                        <div class="flex flex-col items-center space-y-3">
                            <div class="rounded-xl overflow-hidden border border-slate-700 shadow-2xl bg-black max-h-[380px] w-full flex items-center justify-center">
                                <video controls class="max-h-[380px] w-auto rounded-lg" src="${video.url}?t=${Date.now()}" preload="metadata">
                                    متصفحك لا يدعم تشغيل الفيديو مباشرة.
                                </video>
                            </div>
                            <div class="flex items-center justify-between w-full text-xs text-slate-400 px-1 pt-1">
                                <span><i class="fa-solid fa-file-video text-indigo-400 ml-1"></i>${video.filename} (${video.size_mb} MB)</span>
                                <a href="${video.url}" download="${video.filename}" class="px-3.5 py-1.5 rounded-lg bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 font-bold transition flex items-center space-x-1 space-x-reverse">
                                    <i class="fa-solid fa-download"></i>
                                    <span>تحميل الفيديو MP4</span>
                                </a>
                            </div>
                        </div>
                    ` : `
                        <div class="p-8 text-center bg-slate-900/60 rounded-xl border border-dashed border-slate-800 space-y-3">
                            <div class="w-12 h-12 rounded-full bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto text-xl">
                                <i class="fa-solid fa-clapperboard"></i>
                            </div>
                            <div class="text-slate-300 text-xs font-semibold">لم يتم تجميع ورندر الفيديو النهائي بعد.</div>
                            <p class="text-slate-500 text-[11px]">يتم دمج المشاهد البصرية مع التعليق الصوتي والترجمة الحركية تلقائياً.</p>
                        </div>
                    `}

                    <!-- Video Action Controls -->
                    <div class="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
                        <div class="flex items-center space-x-2 space-x-reverse text-xs">
                            <span class="text-slate-400">الصيغة:</span>
                            <select id="video-render-format" class="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200 text-xs focus:outline-none">
                                <option value="vertical">شورتس وريلز (9:16 عمودي)</option>
                                <option value="horizontal">يوتيوب طويل (16:9 أفقي)</option>
                            </select>
                        </div>
                        <button id="btn-render-video" onclick="triggerVideoRender('${data.idea_id}')" class="px-4 py-2 rounded-xl bg-gradient-to-l from-indigo-500 to-sky-500 hover:from-indigo-400 hover:to-sky-400 text-white font-bold text-xs shadow-md transition flex items-center space-x-2 space-x-reverse">
                            <i class="fa-solid fa-wand-magic-sparkles"></i>
                            <span>${video ? 'إعادة رندر الفيديو' : '🎬 رندر وتجميع الفيديو الآن'}</span>
                        </button>
                    </div>
                </div>

                <!-- VoxArabicStudio Voiceover Engine -->
                <div class="glass-panel p-6 rounded-2xl border border-sky-500/40 relative overflow-hidden bg-gradient-to-b from-slate-900/90 to-sky-950/20 space-y-4">
                    <div class="flex items-center justify-between pb-3 border-b border-slate-800">
                        <div class="flex items-center space-x-2 space-x-reverse text-sky-400 font-bold">
                            <i class="fa-solid fa-microphone-lines text-xl"></i>
                            <span class="text-base">التعليق الصوتي (VoxArabicStudio Engine)</span>
                        </div>
                        <span class="text-[10px] font-bold bg-sky-500/20 text-sky-300 px-2.5 py-1 rounded-full border border-sky-500/30">
                            لهجة مصرية أصيلة 🇪🇬
                        </span>
                    </div>

                    ${audio ? `
                        <div class="space-y-4">
                            <div class="bg-slate-900/90 p-4 rounded-xl border border-slate-800 space-y-3">
                                <div class="flex items-center justify-between text-xs">
                                    <span class="font-bold text-slate-200"><i class="fa-solid fa-circle-check text-emerald-400 ml-1"></i>الصوت المختار: ${audio.voice_name}</span>
                                    <span class="text-slate-400 font-mono text-[11px]">${audio.size_kb} KB</span>
                                </div>
                                <audio controls class="w-full h-10 rounded" src="${audio.url}?t=${Date.now()}" preload="metadata">
                                    متصفحك لا يدعم مشغل الصوت.
                                </audio>
                            </div>
                        </div>
                    ` : `
                        <div class="p-8 text-center bg-slate-900/60 rounded-xl border border-dashed border-slate-800 space-y-3">
                            <div class="w-12 h-12 rounded-full bg-sky-500/10 text-sky-400 flex items-center justify-center mx-auto text-xl">
                                <i class="fa-solid fa-microphone-slash"></i>
                            </div>
                            <div class="text-slate-300 text-xs font-semibold">لم يتم توليد التعليق الصوتي بعد.</div>
                            <p class="text-slate-500 text-[11px]">اختر المعلق الصوتي واضغط توليد لبدء التسجيل الصوتي الاستوديو فوراً.</p>
                        </div>
                    `}

                    <!-- Voice Controls -->
                    <div class="pt-3 border-t border-slate-800/80 space-y-3">
                        <div class="flex flex-wrap items-center justify-between gap-3 text-xs">
                            <div class="flex items-center space-x-2 space-x-reverse">
                                <span class="text-slate-400">المعلق الصوتي:</span>
                                <select id="voice-selector" class="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200 text-xs focus:outline-none">
                                    <option value="shakir">شاكر (استوديو احترافي - صوت إذاعي مصري رجالي)</option>
                                    <option value="salma">سلمى (استوديو إذاعي - صوت مصري طبيعي أنثوي)</option>
                                </select>
                            </div>
                            <button id="btn-generate-voice" onclick="triggerVoiceover('${data.idea_id}')" class="px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs shadow-md transition flex items-center space-x-2 space-x-reverse">
                                <i class="fa-solid fa-microphone"></i>
                                <span>${audio ? 'إعادة تسجيل الصوت' : '🎙️ توليد التعليق الصوتي'}</span>
                            </button>
                        </div>
                        <div class="text-[11px] text-slate-400 flex items-center space-x-1.5 space-x-reverse">
                            <i class="fa-brands fa-github text-slate-500"></i>
                            <span>مبني ومدمج عبر: <a href="https://github.com/ahmedmorgan86/VoxArabicStudio" target="_blank" class="text-sky-400 hover:underline">ahmedmorgan86/VoxArabicStudio</a></span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- SCENE VISUALS STORYBOARD -->
            ${frames.length > 0 ? `
                <div class="glass-panel p-6 rounded-2xl border border-slate-700/60 space-y-4">
                    <div class="flex items-center justify-between pb-3 border-b border-slate-800">
                        <div class="flex items-center space-x-2 space-x-reverse text-emerald-400 font-bold">
                            <i class="fa-solid fa-photo-film text-lg"></i>
                            <span>لوحة مشاهد الفيديو (Scene Visuals & Storyboard)</span>
                        </div>
                        <span class="text-xs text-slate-400">توليد فني 8K بواسطة Pollinations Flux AI</span>
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        ${frames.map((fr, idx) => `
                            <div class="relative group rounded-xl overflow-hidden border border-slate-700 shadow bg-slate-900">
                                <img src="${fr.url}?t=${Date.now()}" alt="${fr.filename}" class="w-full h-44 object-cover transition duration-300 group-hover:scale-105">
                                <div class="absolute bottom-0 inset-x-0 bg-slate-950/80 p-2 text-[11px] text-slate-300 text-center font-bold">
                                    مشهد #${idx + 1}
                                </div>
                                <a href="${fr.url}" target="_blank" class="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-xs font-bold transition">
                                    <i class="fa-solid fa-magnifying-glass-plus ml-1"></i> تكبير
                                </a>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            <!-- Main Production Columns -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Left 2 Cols: Script & Scenes & SEO -->
                <div class="lg:col-span-2 space-y-6">
                    <!-- Script Voiceover Box -->
                    <div class="glass-panel p-6 rounded-2xl border border-slate-700/60">
                        <div class="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
                            <div class="flex items-center space-x-2 space-x-reverse text-sky-400 font-bold">
                                <i class="fa-solid fa-align-right text-lg"></i>
                                <span>السكريبت الكامل والإلقاء الصوتي (باللهجة المصرية)</span>
                            </div>
                            <button onclick="copyText('script-text-content')" class="text-xs text-slate-400 hover:text-sky-300 flex items-center space-x-1 space-x-reverse">
                                <i class="fa-regular fa-copy"></i>
                                <span>نسخ السكريبت</span>
                            </button>
                        </div>
                        <div class="bg-slate-900/80 p-4 rounded-xl border border-slate-800 text-slate-200 text-sm leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto" id="script-text-content">
${data.script_markdown}
                        </div>
                    </div>

                    <!-- 8-Scene Breakdown Grid -->
                    <div class="glass-panel p-6 rounded-2xl border border-slate-700/60">
                        <div class="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
                            <div class="flex items-center space-x-2 space-x-reverse text-indigo-400 font-bold">
                                <i class="fa-solid fa-film text-lg"></i>
                                <span>تفكيك المشاهد الإخراجي (${scenes.length} مشاهد سينمائية)</span>
                            </div>
                            <span class="text-xs text-slate-400">توقيتات دقيقة وبرومبتات فيديو جاهزة</span>
                        </div>

                        <div class="space-y-3 max-h-96 overflow-y-auto pr-1">
                            ${scenes.map(s => `
                                <div class="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
                                    <div class="flex items-center justify-between text-xs">
                                        <span class="font-bold text-sky-400">مشهد #${s.scene_number}</span>
                                        <span class="font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">${s.timecode || '00:00'}</span>
                                        <span class="text-amber-400 font-bold">${s.on_screen_text || ''}</span>
                                    </div>
                                    <p class="text-xs text-slate-300 leading-relaxed font-semibold">🗣️ الإلقاء: "${s.voiceover}"</p>
                                    <div class="grid grid-cols-2 gap-2 text-[11px] text-slate-400 pt-1">
                                        <div><span class="text-slate-500">البصري:</span> ${s.visual_description || ''}</div>
                                        <div><span class="text-slate-500">المؤثرات SFX:</span> ${s.sfx || ''}</div>
                                    </div>
                                    ${s.ai_video_prompt ? `
                                        <div class="mt-1 pt-1.5 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                                            <span class="text-slate-400 truncate max-w-[85%] font-mono text-[10px]">AI Prompt: ${s.ai_video_prompt}</span>
                                            <button onclick="navigator.clipboard.writeText('${s.ai_video_prompt.replace(/'/g, "\\'")}')" class="text-sky-400 hover:text-sky-300 text-xs px-2 py-0.5 rounded bg-sky-500/10">
                                                نسخ
                                            </button>
                                        </div>
                                    ` : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- SEO Multi-Platform Package -->
                    <div class="glass-panel p-6 rounded-2xl border border-slate-700/60 space-y-4">
                        <div class="flex items-center justify-between pb-3 border-b border-slate-800">
                            <div class="flex items-center space-x-2 space-x-reverse text-amber-400 font-bold">
                                <i class="fa-solid fa-tags text-lg"></i>
                                <span>حزمة الكلمات المفتاحية وأوصاف المنصات (SEO Package)</span>
                            </div>
                        </div>

                        <!-- 5 Titles -->
                        <div>
                            <span class="text-xs font-bold text-slate-300 block mb-2">5 عناوين مقترحة للتجربة (A/B Testing):</span>
                            <div class="space-y-1.5">
                                ${(seo.alternative_titles || []).map((t, idx) => `
                                    <div class="p-2 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-200 flex items-center justify-between">
                                        <span><b>#${idx + 1}</b> ${t}</span>
                                        <button onclick="navigator.clipboard.writeText('${t.replace(/'/g, "\\'")}')" class="text-slate-400 hover:text-sky-400">
                                            <i class="fa-regular fa-copy"></i>
                                        </button>
                                    </div>
                                `).join('')}
                            </div>
                        </div>

                        <!-- Tags (20) -->
                        <div>
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-xs font-bold text-slate-300">الكلمات المفتاحية الـ 20 (Tags):</span>
                                <button onclick="navigator.clipboard.writeText('${(seo.tags_20 || []).join(', ')}')" class="text-xs text-sky-400 hover:text-sky-300">
                                    نسخ الـ 20 كلمة معاً
                                </button>
                            </div>
                            <div class="flex flex-wrap gap-1.5">
                                ${(seo.tags_20 || []).map(tg => `
                                    <span class="text-[11px] px-2 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700 tag-pill cursor-pointer" onclick="navigator.clipboard.writeText('${tg}')">
                                        ${tg}
                                    </span>
                                `).join('')}
                            </div>
                        </div>

                        <!-- Pinned Comment -->
                        <div class="bg-slate-900/60 p-3 rounded-xl border border-slate-800 text-xs">
                            <span class="font-bold text-sky-400 block mb-1">📌 التعليق المثبت (Pinned Comment):</span>
                            <p class="text-slate-300">${seo.pinned_comment || ''}</p>
                        </div>
                    </div>
                </div>

                <!-- Right 1 Col: Thumbnails & Covers -->
                <div class="space-y-6">
                    <!-- YouTube 16:9 Thumbnail -->
                    <div class="glass-panel p-5 rounded-2xl border border-slate-700/60 space-y-3">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-slate-200"><i class="fa-brands fa-youtube text-rose-500 ml-1"></i>صورة يوتيوب (16:9)</span>
                            <span class="text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/30">
                                1280×720 (Real AI Art)
                            </span>
                        </div>
                        ${thumbs.youtube_url ? `
                            <div class="relative group rounded-xl overflow-hidden border border-slate-700 shadow-md">
                                <img src="${thumbs.youtube_url}?t=${Date.now()}" alt="YouTube Thumbnail" class="w-full h-auto object-cover transition duration-300 group-hover:scale-105">
                                <a href="${thumbs.youtube_url}" target="_blank" class="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-xs font-bold transition">
                                    <i class="fa-solid fa-arrow-up-right-from-square ml-1"></i> فتح بالحجم الكامل
                                </a>
                            </div>
                        ` : '<div class="py-12 bg-slate-900/50 rounded-xl text-center text-xs text-slate-500">لم يتم توليد الصورة بعد</div>'}
                    </div>

                    <!-- Shorts 9:16 Cover -->
                    <div class="glass-panel p-5 rounded-2xl border border-slate-700/60 space-y-3">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-slate-200"><i class="fa-brands fa-tiktok text-cyan-400 ml-1"></i>غلاف ريلز وشورتس (9:16)</span>
                            <span class="text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/30">
                                1080×1920 (Real AI Art)
                            </span>
                        </div>
                        ${thumbs.vertical_url ? `
                            <div class="relative group rounded-xl overflow-hidden border border-slate-700 shadow-md max-w-[200px] mx-auto">
                                <img src="${thumbs.vertical_url}?t=${Date.now()}" alt="Vertical Shorts Cover" class="w-full h-auto object-cover transition duration-300 group-hover:scale-105">
                                <a href="${thumbs.vertical_url}" target="_blank" class="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-xs font-bold transition">
                                    <i class="fa-solid fa-arrow-up-right-from-square ml-1"></i> فتح بالحجم الكامل
                                </a>
                            </div>
                        ` : '<div class="py-12 bg-slate-900/50 rounded-xl text-center text-xs text-slate-500">لم يتم توليد الغلاف بعد</div>'}
                    </div>

                    <!-- Storage Asset Tree -->
                    <div class="glass-panel p-5 rounded-2xl border border-slate-700/60 space-y-3 text-xs">
                        <span class="font-bold text-slate-300 block"><i class="fa-solid fa-folder-tree text-sky-400 ml-1"></i>هيكل المجلدات المنظم:</span>
                        <div class="space-y-1 font-mono text-[11px] text-slate-400 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                            <div>📁 /AI Content Factory/2026/${data.idea_id}/</div>
                            <div class="mr-3">├── 📂 Research/</div>
                            <div class="mr-3">├── 📂 Scripts/ (Markdown + JSON)</div>
                            <div class="mr-3">├── 📂 SEO/ (Titles, Tags, Descriptions)</div>
                            <div class="mr-3">├── 📂 Thumbnails/ (1280x720 + 1080x1920)</div>
                            <div class="mr-3">├── 📂 Audio/ (VoxArabic Egyptian Voiceover)</div>
                            <div class="mr-3">├── 📂 Video_Assets/ (Final Rendered MP4 + Frames)</div>
                            <div class="mr-3">└── 📂 Publishing/ (Manifests)</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Action: Run production for idea
async function runProductionForSelected(ideaId) {
    showToast(`بدء دورة الإنتاج للفكرة ${ideaId}... قد تستغرق بضع ثوانٍ.`, 'info');
    try {
        const res = await fetch('/api/production/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idea_id: ideaId })
        });
        if (!res.ok) {
            const errBody = await res.text();
            throw new Error(`(${res.status}): ${errBody || res.statusText}`);
        }
        const data = await res.json();
        if (data.success) {
            showToast(`تم إنتاج جميع أصول الفكرة بنجاح!`, 'success');
            await openStudio(ideaId);
            await loadIdeas();
            await loadOverview();
        } else {
            showToast(`فشل الإنتاج: ${data.detail}`, 'error');
        }
    } catch (err) {
        showToast(`خطأ في العملية: ${err.message}`, 'error');
    }
}

// Action: Approve Publishing
async function approvePublishing(ideaId) {
    try {
        const res = await fetch('/api/publishing/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idea_id: ideaId, approved: true })
        });
        const data = await res.json();
        if (data.status === 'SUCCESS_PREPARED') {
            showToast('تم اعتماد حزمة الفيديو وتجهيز النشر للمنصات الخمس بنجاح!', 'success');
            await openStudio(ideaId);
            await loadOverview();
        } else {
            showToast(`حالة الاعتماد: ${data.message || data.status}`, 'error');
        }
    } catch (err) {
        showToast(`خطأ: ${err.message}`, 'error');
    }
}

// Action: Trigger VoxArabic Voiceover
async function triggerVoiceover(ideaId) {
    const selector = document.getElementById('voice-selector');
    const voiceKey = selector ? selector.value : 'shakir';
    const btn = document.getElementById('btn-generate-voice');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>جارٍ التسجيل الصوتي...</span>';
    }
    showToast(`جارٍ توليد التعليق الصوتي باللهجة المصرية عبر VoxArabicStudio...`, 'info');
    try {
        const res = await fetch('/api/voice/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idea_id: ideaId, voice_key: voiceKey })
        });
        if (!res.ok) {
            const err = await res.text();
            throw new Error(err || res.statusText);
        }
        const data = await res.json();
        showToast('تم إنتاج التعليق الصوتي بنجاح!', 'success');
        await openStudio(ideaId);
    } catch (err) {
        showToast(`فشل توليد الصوت: ${err.message}`, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
        }
    }
}

// Action: Trigger Video Render
async function triggerVideoRender(ideaId) {
    const formatSelector = document.getElementById('video-render-format');
    const isVertical = formatSelector ? formatSelector.value === 'vertical' : true;
    const voiceSelector = document.getElementById('voice-selector');
    const voiceKey = voiceSelector ? voiceSelector.value : 'shakir';
    const btn = document.getElementById('btn-render-video');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>جارٍ تجميع ورندر الفيديو...</span>';
    }
    showToast(`جارٍ تجميع ورندر الفيديو الكامل (${isVertical ? 'Shorts 9:16' : '16:9'})... يرجى الانتظار ثوانٍ`, 'info');
    try {
        const res = await fetch('/api/video/render', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idea_id: ideaId, voice_key: voiceKey, is_vertical: isVertical })
        });
        if (!res.ok) {
            const err = await res.text();
            throw new Error(err || res.statusText);
        }
        const data = await res.json();
        showToast('🎉 تم رندر وتجميع الفيديو النهائي بنجاح وجاهز للنشر!', 'success');
        await openStudio(ideaId);
    } catch (err) {
        showToast(`فشل رندر الفيديو: ${err.message}`, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
        }
    }
}

// API: Analytics & Digest
async function loadAnalytics() {
    try {
        const res = await fetch('/api/analytics');
        const data = await res.json();
        state.analytics = data;

        // Render Digest Card
        const digestEl = document.getElementById('analytics-digest-box');
        if (digestEl) {
            digestEl.innerHTML = data.weekly_digest;
        }

        // Render Table
        renderAnalyticsTable(data.records);
        renderAnalyticsChart();
    } catch (err) {
        console.error('Error loading analytics:', err);
    }
}

function renderAnalyticsTable(records) {
    const container = document.getElementById('analytics-records-tbody');
    if (!container) return;
    if (!records || records.length === 0) {
        container.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-slate-500">لا توجد سجلات أداء بعد.</td></tr>';
        return;
    }

    container.innerHTML = records.map(r => `
        <tr class="border-b border-slate-800 hover:bg-slate-800/30 transition text-xs">
            <td class="p-3 font-mono text-slate-400">${r['Record ID'] || '-'}</td>
            <td class="p-3 font-semibold text-slate-200">${r['Video Title'] || '-'}</td>
            <td class="p-3"><span class="px-2 py-0.5 rounded bg-slate-800 text-sky-400 font-bold">${r['Platform'] || 'YouTube'}</span></td>
            <td class="p-3 font-bold text-white">${Number(r['Views'] || 0).toLocaleString()}</td>
            <td class="p-3 text-emerald-400 font-bold">${r['CTR (%)'] || '0'}%</td>
            <td class="p-3 font-bold text-amber-400">${r['AI Performance Score'] || '8.5/10'}</td>
            <td class="p-3 text-slate-400">${r['Recorded Date'] || '-'}</td>
        </tr>
    `).join('');
}

function renderAnalyticsChart() {
    if (!state.analytics || !state.analytics.records) return;
    const canvas = document.getElementById('analyticsChart');
    if (!canvas) return;

    const records = state.analytics.records;
    const labels = records.map(r => (r['Video Title'] || '').substring(0, 18) + '...');
    const viewsData = records.map(r => Number(r['Views'] || 0));
    const ctrData = records.map(r => Number(r['CTR (%)'] || 0));

    if (state.chartInstance) {
        state.chartInstance.destroy();
    }

    const ctx = canvas.getContext('2d');
    state.chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'المشاهدات (Views)',
                    data: viewsData,
                    backgroundColor: 'rgba(56, 189, 248, 0.7)',
                    borderColor: '#38bdf8',
                    borderWidth: 1,
                    yAxisID: 'y',
                    borderRadius: 6
                },
                {
                    label: 'نسبة النقر للظهور CTR (%)',
                    data: ctrData,
                    type: 'line',
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.2)',
                    borderWidth: 2,
                    yAxisID: 'y1',
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8', font: { family: 'Cairo' } }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#64748b', font: { family: 'Cairo', size: 10 } },
                    grid: { color: 'rgba(51, 65, 85, 0.2)' }
                },
                y: {
                    type: 'linear',
                    position: 'left',
                    ticks: { color: '#38bdf8' },
                    grid: { color: 'rgba(51, 65, 85, 0.2)' }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    ticks: { color: '#f59e0b' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

// Action: Refresh Weekly Digest
async function triggerRefreshAnalytics() {
    showToast('جاري إعادة احتساب التحليلات وتحديث التقرير الأسبوعي...', 'info');
    try {
        const res = await fetch('/api/analytics/refresh', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast('تم تحديث التحليلات والتقرير الأسبوعي بنجاح!', 'success');
            await loadAnalytics();
            await loadOverview();
        }
    } catch (err) {
        showToast(`خطأ: ${err.message}`, 'error');
    }
}

// Action: Copy Digest
function copyDigestText() {
    const el = document.getElementById('analytics-digest-box');
    if (!el) return;
    const text = el.innerText || el.textContent;
    navigator.clipboard.writeText(text);
    showToast('تم نسخ التقرير الأسبوعي بصيغة جاهزة لتليجرام!', 'success');
}

// API: Settings
async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        const data = await res.json();
        state.settings = data;
        const container = document.getElementById('settings-list');
        if (!container) return;

        container.innerHTML = Object.keys(data).map(key => {
            const item = data[key];
            return `
                <div class="glass-panel p-4 rounded-xl border border-slate-700/60 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
                    <div class="md:w-1/3">
                        <span class="font-mono text-sky-400 font-bold block">${key}</span>
                        <p class="text-slate-400 text-[11px]">${item.description || ''}</p>
                    </div>
                    <div class="md:w-1/2">
                        <input type="text" id="setting-${key}" value="${item.value}" class="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-sky-500 font-mono text-xs">
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        console.error('Error loading settings:', err);
    }
}

async function saveAllSettings() {
    const payload = {};
    Object.keys(state.settings).forEach(key => {
        const input = document.getElementById(`setting-${key}`);
        if (input) {
            payload[key] = input.value;
        }
    });

    try {
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            showToast('تم حفظ الإعدادات وتطبيقها بنجاح!', 'success');
            await loadSettings();
            await loadOverview();
        }
    } catch (err) {
        showToast(`خطأ في الحفظ: ${err.message}`, 'error');
    }
}

// Action: Run Full End-to-End Automation Cycle
async function runFullPipelineCycle() {
    const btn = document.getElementById('btn-run-full-cycle');
    if (btn) btn.disabled = true;
    showToast('بدء تشغيل دورة الأوتوميشن الشاملة من الألف إلى الياء...', 'info');

    try {
        const res = await fetch('/api/pipeline/run-full-cycle', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(`تم إتمام دورة الإنتاج بالكامل للفكرة: ${data.title}!`, 'success');
            await loadOverview();
            await loadIdeas();
            await loadAnalytics();
            await openStudio(data.idea_id);
        } else {
            showToast(`فشلت الدورة: ${data.detail}`, 'error');
        }
    } catch (err) {
        showToast(`خطأ: ${err.message}`, 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
}

function copyText(elemId) {
    const el = document.getElementById(elemId);
    if (!el) return;
    navigator.clipboard.writeText(el.innerText || el.textContent);
    showToast('تم النسخ إلى الحافظة!', 'success');
}
