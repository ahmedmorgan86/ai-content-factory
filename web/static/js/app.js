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

function apiFetch(input, init = {}) {
    const headers = new Headers(init.headers || {});
    const token = sessionStorage.getItem('medad_admin_token');
    if (token) headers.set('Authorization', `Bearer ${token}`);
    return fetch(input, { ...init, headers });
}

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    const savedToken = sessionStorage.getItem('medad_admin_token');
    const panel = document.getElementById('admin-access-panel');
    const errorMessage = document.getElementById('admin-access-error');
    const beginApp = () => {
        panel?.classList.add('hidden');
        loadOverview(); loadIdeas(); loadAnalytics(); loadSettings();
    };
    const requestAuthStatus = apiFetch('/api/auth/status').then(response => {
        if (!response.ok) throw new Error('تعذر التحقق من حالة تسجيل الدخول');
        return response.json();
    });
    requestAuthStatus.then(({ required }) => {
        if (!required) beginApp();
        else if (savedToken) {
            apiFetch('/api/settings').then(response => {
                if (response.ok) beginApp();
                else {
                    sessionStorage.removeItem('medad_admin_token');
                    panel?.classList.remove('hidden');
                    if (errorMessage) errorMessage.textContent = 'انتهت صلاحية الجلسة أو الرمز غير صحيح. أدخل رمز الإدارة مرة أخرى.';
                }
            }).catch(() => {
                panel?.classList.remove('hidden');
                if (errorMessage) errorMessage.textContent = 'تعذر الاتصال بالخادم. أعد المحاولة بعد قليل.';
            });
        } else panel?.classList.remove('hidden');
    }).catch(() => {
        panel?.classList.remove('hidden');
        if (errorMessage) errorMessage.textContent = 'تعذر التحقق من إعدادات الدخول. حدّث الصفحة وحاول مرة أخرى.';
    });
    document.getElementById('admin-access-submit')?.addEventListener('click', async () => {
        const field = document.getElementById('admin-access-token');
        const token = field?.value || '';
        if (!token) {
            if (errorMessage) errorMessage.textContent = 'أدخل رمز الإدارة أولًا.';
            field?.focus();
            return;
        }
        if (errorMessage) errorMessage.textContent = '';
        sessionStorage.setItem('medad_admin_token', token);
        try {
            const response = await apiFetch('/api/settings');
            if (!response.ok) throw new Error('رمز الدخول غير صحيح');
            field.value = '';
            beginApp();
        } catch (error) {
            sessionStorage.removeItem('medad_admin_token');
            if (errorMessage) errorMessage.textContent = error.message || 'تعذر تسجيل الدخول. حاول مرة أخرى.';
            field?.focus();
        }
    });
    document.getElementById('admin-access-token')?.addEventListener('keydown', event => {
        if (event.key === 'Enter') document.getElementById('admin-access-submit')?.click();
    });
});

function escapeHtml(value) {
    const element = document.createElement('span');
    element.textContent = value == null ? '' : String(value);
    return element.innerHTML;
}

// Toast Notifications
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    const bg = type === 'success' ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300' :
               type === 'error' ? 'bg-rose-500/20 border-rose-500/50 text-rose-300' :
               'bg-sky-500/20 border-sky-500/50 text-sky-300';
    const icon = type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-triangle-exclamation' : 'fa-info-circle';
    
    toast.className = `glass-panel border px-4 py-3 rounded-xl flex items-center space-x-3 space-x-reverse text-sm shadow-xl toast-animate ${bg}`;
    const iconElement = document.createElement('i');
    iconElement.className = `fa-solid ${icon} text-lg`;
    iconElement.setAttribute('aria-hidden', 'true');
    const messageElement = document.createElement('span');
    messageElement.textContent = message;
    toast.append(iconElement, messageElement);
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
        tab.addEventListener('keydown', (event) => {
            const order = Array.from(tabs);
            const index = order.indexOf(tab);
            let nextIndex = index;
            if (event.key === 'ArrowLeft') nextIndex = (index + 1) % order.length;
            else if (event.key === 'ArrowRight') nextIndex = (index - 1 + order.length) % order.length;
            else if (event.key === 'Home') nextIndex = 0;
            else if (event.key === 'End') nextIndex = order.length - 1;
            else return;
            event.preventDefault();
            order[nextIndex].focus();
            switchTab(order[nextIndex].dataset.tab);
        });
        tab.tabIndex = tab.getAttribute('aria-selected') === 'true' ? 0 : -1;
    });

    document.addEventListener('click', async (event) => {
        const openButton = event.target.closest('[data-open-idea]');
        if (openButton) {
            openStudio(openButton.dataset.openIdea);
            return;
        }
        const actionButton = event.target.closest('[data-action][data-idea-id]');
        if (actionButton) {
            const { action, ideaId } = actionButton.dataset;
            if (action === 'produce') runProductionForSelected(ideaId);
            else if (action === 'approve') approvePublishing(ideaId);
            else if (action === 'render') triggerVideoRender(ideaId);
            else if (action === 'voice') triggerVoiceover(ideaId);
            return;
        }
        const copyButton = event.target.closest('[data-copy-text]');
        if (copyButton) {
            try {
                await navigator.clipboard.writeText(copyButton.dataset.copyText || '');
                showToast('تم النسخ.', 'success');
            } catch (_) {
                showToast('تعذر النسخ؛ تحقق من صلاحية الحافظة في المتصفح.', 'error');
            }
        }
    });
    document.addEventListener('keydown', (event) => {
        const card = event.target.closest('[data-open-idea][role="button"]');
        if (card && (event.key === 'Enter' || event.key === ' ')) {
            event.preventDefault();
            openStudio(card.dataset.openIdea);
        }
    });
    switchTab('dashboard');
}

function switchTab(tabId) {
    state.currentTab = tabId;
    const activeEl = document.activeElement;
    document.querySelectorAll('.tab-content').forEach(section => {
        if (activeEl && section.contains(activeEl)) {
            const tabButton = document.getElementById(`nav-tab-${tabId}`);
            if (tabButton) tabButton.focus();
            else if (activeEl.blur) activeEl.blur();
        }
        section.classList.add('hidden');
        section.setAttribute('aria-hidden', 'true');
        section.setAttribute('inert', '');
    });
    const targetSection = document.getElementById(`tab-${tabId}`);
    if (targetSection) {
        targetSection.classList.remove('hidden');
        targetSection.setAttribute('role', 'tabpanel');
        targetSection.tabIndex = 0;
        targetSection.setAttribute('aria-labelledby', `nav-tab-${tabId}`);
        targetSection.setAttribute('aria-hidden', 'false');
        targetSection.removeAttribute('inert');
    }

    document.querySelectorAll('.nav-tab').forEach(tab => {
        const selected = tab.dataset.tab === tabId;
        tab.setAttribute('aria-selected', String(selected));
        tab.tabIndex = selected ? 0 : -1;
    });

    if (tabId === 'analytics') {
        renderAnalyticsChart();
    }
}

// API: Overview
async function loadOverview() {
    try {
        const res = await apiFetch('/api/overview'); if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        state.overview = data;
        
        // Update KPI Cards
        document.getElementById('kpi-total-ideas').textContent = data.kpis.total_ideas;
        document.getElementById('kpi-ready-packages').textContent = data.kpis.ready_packages;
        document.getElementById('kpi-total-views').textContent = data.kpis.has_analytics ? data.kpis.total_views.toLocaleString() : '—';
        document.getElementById('kpi-avg-ctr').textContent = data.kpis.has_analytics ? data.kpis.avg_ctr + '%' : '—';
        document.getElementById('kpi-subscribers').textContent = data.kpis.has_analytics ? '+' + data.kpis.total_subscribers.toLocaleString() : '—';
        document.getElementById('kpi-watch-hours').textContent = data.kpis.has_analytics ? data.kpis.total_watch_hours.toLocaleString() + ' س' : '—';
        const healthEl = document.getElementById('data-health-summary');
        if (healthEl) healthEl.textContent = `البيانات: ${data.data_store?.provider || 'غير محدد'} · الملفات: ${data.file_store?.provider || 'غير محدد'}`;
        
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
        <div class="p-3 rounded-xl bg-slate-800/50 border border-slate-700/60 flex items-center justify-between hover:border-sky-500/40 transition cursor-pointer" data-open-idea="${escapeHtml(i['Idea ID'] || i.idea_id)}" role="button" tabindex="0">
            <div class="flex items-center space-x-3 space-x-reverse">
                <span class="px-2 py-0.5 rounded text-xs font-bold ${(i['Video Type'] || i.video_type) === 'Long-form' ? 'bg-indigo-500/20 text-indigo-300' : 'bg-emerald-500/20 text-emerald-300'}">
                    ${(i['Video Type'] || i.video_type) === 'Long-form' ? 'فيديو طويل' : 'شورتس'}
                </span>
                <div>
                    <h4 class="text-sm font-semibold text-slate-200 line-clamp-1">${escapeHtml(i['Video Title'] || i.video_title)}</h4>
                    <p class="text-xs text-slate-400">الجمهور: ${escapeHtml(i['Target Audience'] || i.target_audience || 'الجميع')}</p>
                </div>
            </div>
            <div class="flex items-center space-x-2 space-x-reverse">
                <span class="text-xs font-bold text-amber-400"><i class="fa-solid fa-star text-[10px] ml-1" aria-hidden="true"></i>${escapeHtml(i['Priority Score'] || i.priority_score || '—')}</span>
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
        let url = `/api/ideas?type=${encodeURIComponent(filterType)}`;
        if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;
        const res = await apiFetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
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
                        <span class="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">${escapeHtml(item['Idea ID'] || item.idea_id)}</span>
                        <span class="px-2 py-0.5 rounded text-xs font-semibold ${(item['Video Type'] || item.video_type) === 'Long-form' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'}">
                            ${(item['Video Type'] || item.video_type) === 'Long-form' ? '🎥 طويل (8-12 د)' : '⚡ شورتس (60 ث)'}
                        </span>
                    </div>
                    <div class="flex items-center space-x-1 space-x-reverse bg-amber-500/10 text-amber-300 border border-amber-500/30 px-2.5 py-0.5 rounded-full text-xs font-bold">
                        <i class="fa-solid fa-star text-[10px]"></i>
                        <span>${escapeHtml(item['Priority Score'] || item.priority_score || '—')} / 10</span>
                    </div>
                </div>

                <h3 class="font-bold text-base text-slate-100 mb-2 leading-snug">${escapeHtml(item['Video Title'] || item.video_title)}</h3>
                <p class="text-xs text-slate-400 line-clamp-2 mb-3 leading-relaxed">${escapeHtml(item['Video Summary'] || item.video_summary || '')}</p>

                <div class="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/80 mb-3 text-xs">
                    <span class="text-sky-400 font-bold block mb-1">🎯 الخطاف (0-3 ثوانٍ):</span>
                    <p class="text-slate-300 italic line-clamp-2">"${escapeHtml(item['Hook'] || item.hook || '')}"</p>
                </div>
            </div>

            <div>
                <div class="flex flex-wrap gap-1.5 mb-4">
                    ${(item['SEO Keywords'] || (Array.isArray(item.seo_keywords) ? item.seo_keywords.join(', ') : item.seo_keywords) || '').split(',').slice(0, 3).map(k => `
                        <span class="text-[11px] px-2 py-0.5 rounded-md bg-slate-800/90 text-slate-400 border border-slate-700/80">#${escapeHtml(k.trim())}</span>
                    `).join('')}
                </div>

                <div class="pt-3 border-t border-slate-800 flex items-center justify-between">
                    <span class="text-xs ${(item['Status'] || item.status) === 'New' ? 'text-sky-400' : 'text-emerald-400'} font-semibold">
                        <i class="fa-solid fa-circle text-[8px] ml-1" aria-hidden="true"></i>${escapeHtml(item['Status'] || item.status || 'New')}
                    </span>
                    <button type="button" data-open-idea="${escapeHtml(item['Idea ID'] || item.idea_id)}" class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-gradient-to-l from-sky-500 to-indigo-600 text-white hover:from-sky-400 hover:to-indigo-500 shadow-md transition flex items-center space-x-1.5 space-x-reverse">
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
        const res = await apiFetch('/api/ideas/generate', { method: 'POST' });
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
        const res = await apiFetch(`/api/production/${encodeURIComponent(ideaId)}`);
        if (!res.ok) {
            const errBody = await res.text();
            throw new Error(`خطأ (${res.status}): ${errBody || res.statusText}`);
        }
        const data = await res.json();
        state.currentProduction = data;
        renderStudioPackage(data);
    } catch (err) {
        container.innerHTML = `<div class="p-6 text-center text-rose-400">فشل في تحميل حزمة الإنتاج: ${escapeHtml(err.message)}</div>`;
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
                <h3 class="text-xl font-bold text-white mb-2">${escapeHtml(idea['Video Title'] || 'فكرة مختارة')}</h3>
                <p class="text-slate-400 text-sm mb-6">${escapeHtml(idea['Video Summary'] || 'ابدأ إعداد عناصر الإنتاج لهذه الفكرة.')}</p>
                <div class="flex items-center justify-center gap-3">
                    <button type="button" data-action="produce" data-idea-id="${escapeHtml(data.idea_id)}" class="px-6 py-2.5 rounded-xl bg-gradient-to-l from-sky-500 to-indigo-600 text-white font-bold text-sm shadow-lg hover:from-sky-400 hover:to-indigo-500 transition flex items-center space-x-2 space-x-reverse">
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
                        <span class="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-sky-400 border border-slate-700 font-bold">${escapeHtml(data.idea_id)}</span>
                        <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            <i class="fa-solid fa-check-double ml-1"></i>حزمة الإنتاج محفوظة
                        </span>
                        ${video ? `
                            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                <i class="fa-solid fa-clapperboard ml-1"></i>ملف فيديو مجمّع · راجعه قبل الاستخدام
                            </span>
                        ` : ''}
                        <span class="text-xs text-slate-400 font-mono">${escapeHtml(data.storage_path)}</span>
                    </div>
                    <h2 class="text-xl font-bold text-white leading-tight">${escapeHtml(meta['Video Title'] || seo['recommended_best_title'])}</h2>
                </div>
                <div class="flex flex-wrap items-center gap-3">
                    <button type="button" data-action="approve" data-idea-id="${escapeHtml(data.idea_id)}" class="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg transition flex items-center space-x-2 space-x-reverse">
                        <i class="fa-solid fa-circle-check"></i>
                        <span>اعتماد وتجهيز ملفات النشر</span>
                    </button>
                    <button type="button" data-action="produce" data-idea-id="${escapeHtml(data.idea_id)}" class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition flex items-center space-x-2 space-x-reverse">
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
                            <span class="text-base">معاينة ملف الفيديو</span>
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
                                <video controls class="max-h-[380px] w-auto rounded-lg" src="${escapeHtml(video.url)}?t=${Date.now()}" preload="metadata" aria-label="معاينة الفيديو">
                                    متصفحك لا يدعم تشغيل الفيديو مباشرة.
                                </video>
                            </div>
                            <div class="flex items-center justify-between w-full text-xs text-slate-400 px-1 pt-1">
                                <span><i class="fa-solid fa-file-video text-indigo-400 ml-1"></i>${escapeHtml(video.filename)} (${escapeHtml(video.size_mb)} MB)</span>
                                <a href="${escapeHtml(video.url)}" download="${escapeHtml(video.filename)}" class="px-3.5 py-1.5 rounded-lg bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 font-bold transition flex items-center space-x-1 space-x-reverse">
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
                            <p class="text-slate-500 text-[11px]">يمكن إنشاء معاينة فيديو من الإطارات الثابتة والتعليق الصوتي.</p>
                        </div>
                    `}

                    <!-- Video Action Controls -->
                    <div class="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
                        <div class="flex items-center space-x-2 space-x-reverse text-xs">
                            <span class="text-slate-400">الصيغة:</span>
                            <select id="video-render-format" class="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200 text-xs focus:outline-none" onchange="syncVoiceForVideoType()">
                                <option value="vertical">شورتس وريلز (9:16 عمودي)</option>
                                <option value="horizontal">يوتيوب طويل (16:9 أفقي)</option>
                            </select>
                        </div>
                        <button id="btn-render-video" type="button" data-action="render" data-idea-id="${escapeHtml(data.idea_id)}" class="px-4 py-2 rounded-xl bg-gradient-to-l from-indigo-500 to-sky-500 hover:from-indigo-400 hover:to-sky-400 text-white font-bold text-xs shadow-md transition flex items-center space-x-2 space-x-reverse">
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
                            <span class="text-base">التعليق الصوتي (VoxArabicStudio + Google Gemini)</span>
                        </div>
                        <span class="text-[10px] font-bold bg-sky-500/20 text-sky-300 px-2.5 py-1 rounded-full border border-sky-500/30">
                            Google Gemini TTS • مصري 🇪🇬
                        </span>
                    </div>

                    ${audio ? `
                        <div class="space-y-4">
                            <div class="bg-slate-900/90 p-4 rounded-xl border border-slate-800 space-y-3">
                                <div class="flex items-center justify-between text-xs">
                                    <span class="font-bold text-slate-200"><i class="fa-solid fa-circle-check text-emerald-400 ml-1"></i>الصوت المختار: ${escapeHtml(audio.voice_name)}</span>
                                    <span class="text-slate-400 font-mono text-[11px]">${escapeHtml(audio.size_kb)} KB</span>
                                </div>
                                <audio controls class="w-full h-10 rounded" src="${escapeHtml(audio.url)}?t=${Date.now()}" preload="metadata" aria-label="معاينة التعليق الصوتي">
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
                                <select id="voice-selector" class="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200 text-xs focus:outline-none" onchange="syncVoiceForVideoType()">
                                    <option value="google_puck">Google Puck (مصري حيوي للشورتس)</option>
                                    <option value="google_charon">Google Charon (مصري عميق للفيديو الطويل)</option>
                                    <option value="google_kore">Google Kore (مصري واضح وودود)</option>
                                    <option value="google_fenrir">Google Fenrir (مصري قوي وحماسي)</option>
                                    <option value="google_zephyr">Google Zephyr (مصري هادئ)</option>
                                    <option value="shakir">شاكر (Edge TTS - رجالي)</option>
                                    <option value="salma">سلمى (Edge TTS - أنثوي)</option>
                                </select>
                            </div>
                            <button id="btn-generate-voice" type="button" data-action="voice" data-idea-id="${escapeHtml(data.idea_id)}" class="px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs shadow-md transition flex items-center space-x-2 space-x-reverse">
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
${escapeHtml(data.script_markdown)}
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
                                        <span class="font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">${escapeHtml(s.timecode || '00:00')}</span>
                                        <span class="text-amber-400 font-bold">${escapeHtml(s.on_screen_text || '')}</span>
                                    </div>
                                    <p class="text-xs text-slate-300 leading-relaxed font-semibold">🗣️ الإلقاء: "${escapeHtml(s.voiceover)}"</p>
                                    <div class="grid grid-cols-2 gap-2 text-[11px] text-slate-400 pt-1">
                                        <div><span class="text-slate-500">البصري:</span> ${escapeHtml(s.visual_description || '')}</div>
                                        <div><span class="text-slate-500">المؤثرات SFX:</span> ${escapeHtml(s.sfx || '')}</div>
                                    </div>
                                    ${s.ai_video_prompt ? `
                                        <div class="mt-1 pt-1.5 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                                            <span class="text-slate-400 truncate max-w-[85%] font-mono text-[10px]">AI Prompt: ${escapeHtml(s.ai_video_prompt)}</span>
                                            <button data-copy-text="${escapeHtml(s.ai_video_prompt)}" class="text-sky-400 hover:text-sky-300 text-xs px-2 py-0.5 rounded bg-sky-500/10">
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
                                        <span><b>#${idx + 1}</b> ${escapeHtml(t)}</span>
                                        <button data-copy-text="${escapeHtml(t)}" class="text-slate-400 hover:text-sky-400">
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
                                <button data-copy-text="${escapeHtml((seo.tags_20 || []).join(', '))}" class="text-xs text-sky-400 hover:text-sky-300">
                                    نسخ الـ 20 كلمة معاً
                                </button>
                            </div>
                            <div class="flex flex-wrap gap-1.5">
                                ${(seo.tags_20 || []).map(tg => `
                                    <span class="text-[11px] px-2 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700 tag-pill cursor-pointer" data-copy-text="${escapeHtml(tg)}">
                                        ${escapeHtml(tg)}
                                    </span>
                                `).join('')}
                            </div>
                        </div>

                        <!-- Pinned Comment -->
                        <div class="bg-slate-900/60 p-3 rounded-xl border border-slate-800 text-xs">
                            <span class="font-bold text-sky-400 block mb-1">📌 التعليق المثبت (Pinned Comment):</span>
                            <p class="text-slate-300">${escapeHtml(seo.pinned_comment || '')}</p>
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
                                1280×720 (صورة مصغّرة)
                            </span>
                        </div>
                        ${thumbs.youtube_url ? `
                            <div class="relative group rounded-xl overflow-hidden border border-slate-700 shadow-md">
                                <img src="${escapeHtml(thumbs.youtube_url)}?t=${Date.now()}" alt="YouTube Thumbnail" class="w-full h-auto object-cover transition duration-300 group-hover:scale-105">
                                <a href="${escapeHtml(thumbs.youtube_url)}" target="_blank" rel="noopener noreferrer" class="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-xs font-bold transition">
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
                                1080×1920 (غلاف رأسي)
                            </span>
                        </div>
                        ${thumbs.vertical_url ? `
                            <div class="relative group rounded-xl overflow-hidden border border-slate-700 shadow-md max-w-[200px] mx-auto">
                                <img src="${escapeHtml(thumbs.vertical_url)}?t=${Date.now()}" alt="Vertical Shorts Cover" class="w-full h-auto object-cover transition duration-300 group-hover:scale-105">
                                <a href="${escapeHtml(thumbs.vertical_url)}" target="_blank" rel="noopener noreferrer" class="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-xs font-bold transition">
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
        const res = await apiFetch('/api/production/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idea_id: ideaId })
        });
        if (!res.ok) {
            let message = res.statusText;
            try {
                const errorData = await res.json();
                message = errorData.detail || errorData.message || message;
            } catch (_) {
                const errBody = await res.text();
                message = errBody || message;
            }
            throw new Error(`(${res.status}): ${message}`);
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
        const res = await apiFetch('/api/publishing/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idea_id: ideaId, approved: true })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || data.message || res.statusText);
        if (data.status === 'SUCCESS_PREPARED') {
            showToast('تم اعتماد الحزمة وتجهيز ملفاتها. النشر للمنصة يتم بعد ربط الحساب وإتمام خطواتها.', 'success');
            await openStudio(ideaId);
            await loadOverview();
        } else {
            showToast(`حالة الاعتماد: ${data.message || data.status}`, 'error');
        }
    } catch (err) {
        showToast(`خطأ: ${err.message}`, 'error');
    }
}

function syncVoiceForVideoType() {
    const formatSelector = document.getElementById('video-render-format');
    const voiceSelector = document.getElementById('voice-selector');
    if (!formatSelector || !voiceSelector) return;
    const longForm = formatSelector.value === 'horizontal';
    const current = voiceSelector.value;
    if (current === 'google_puck' || current === 'google_charon') {
        voiceSelector.value = longForm ? 'google_charon' : 'google_puck';
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
    showToast(`جارٍ توليد التعليق الصوتي المصري عبر Google Gemini TTS...`, 'info');
    try {
        const res = await apiFetch('/api/voice/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idea_id: ideaId, voice_key: voiceKey })
        });
        if (!res.ok) {
            const err = await res.text();
            let detail = err || res.statusText;
            try { detail = JSON.parse(err).detail || detail; } catch (_) {}
            throw new Error(detail);
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
        const res = await apiFetch('/api/video/render', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idea_id: ideaId, voice_key: voiceKey, is_vertical: isVertical })
        });
        if (!res.ok) {
            const err = await res.text();
            let detail = err || res.statusText;
            try { detail = JSON.parse(err).detail || detail; } catch (_) {}
            throw new Error(detail);
        }
        const data = await res.json();
        showToast('تم تركيب ملف المعاينة بنجاح. راجعه وأكمل النشر يدويًا من المنصة.', 'success');
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
        const res = await apiFetch('/api/analytics'); if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        state.analytics = data;

        // Render Digest Card
        const digestEl = document.getElementById('analytics-digest-box');
        if (digestEl) {
            digestEl.textContent = data.weekly_digest;
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
            <td class="p-3 font-mono text-slate-400">${escapeHtml(r['Record ID'] || '-')}</td>
            <td class="p-3 font-semibold text-slate-200">${escapeHtml(r['Video Title'] || '-')}</td>
            <td class="p-3"><span class="px-2 py-0.5 rounded bg-slate-800 text-sky-400 font-bold">${escapeHtml(r['Platform'] || 'YouTube')}</span></td>
            <td class="p-3 font-bold text-white">${Number(r['Views'] || 0).toLocaleString()}</td>
            <td class="p-3 text-emerald-400 font-bold">${escapeHtml(r['CTR (%)'] || '0')}%</td>
            <td class="p-3 font-bold text-amber-400">${escapeHtml(r['AI Performance Score'] || '—')}</td>
            <td class="p-3 text-slate-400">${escapeHtml(r['Recorded Date'] || '-')}</td>
        </tr>
    `).join('');
}

function renderAnalyticsChart() {
    if (!state.analytics || !state.analytics.records) return;
    const canvas = document.getElementById('analyticsChart');
    if (!canvas) return;

    const records = state.analytics.records;
    if (!records.length) {
        if (state.chartInstance) state.chartInstance.destroy();
        state.chartInstance = null;
        return;
    }
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
                    backgroundColor: 'rgba(48, 72, 58, 0.7)',
                    borderColor: '#30483a',
                    borderWidth: 1,
                    yAxisID: 'y',
                    borderRadius: 6
                },
                {
                    label: 'نسبة النقر للظهور CTR (%)',
                    data: ctrData,
                    type: 'line',
                    borderColor: '#b75e43',
                    backgroundColor: 'rgba(183, 94, 67, 0.16)',
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
                    labels: { color: '#94a3b8', font: { family: 'Tahoma' } }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#64748b', font: { family: 'Tahoma', size: 10 } },
                    grid: { color: 'rgba(51, 65, 85, 0.2)' }
                },
                y: {
                    type: 'linear',
                    position: 'left',
                    ticks: { color: '#30483a' },
                    grid: { color: 'rgba(51, 65, 85, 0.2)' }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    ticks: { color: '#b75e43' },
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
        const res = await apiFetch('/api/analytics/refresh', { method: 'POST' });
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
    navigator.clipboard.writeText(text).then(() => showToast('تم نسخ التقرير الأسبوعي.', 'success'))
        .catch(() => showToast('تعذر النسخ؛ تحقق من صلاحية الحافظة في المتصفح.', 'error'));
}

// API: Settings
async function loadSettings() {
    try {
        const [settingsRes, integRes] = await Promise.all([
            apiFetch('/api/settings'),
            apiFetch('/api/integrations/status').catch(() => null)
        ]);
        if (!settingsRes.ok) throw new Error(`HTTP ${settingsRes.status}`);
        const data = await settingsRes.json();
        state.settings = data;
        const container = document.getElementById('settings-list');
        if (container) {
            container.innerHTML = Object.keys(data).map(key => {
                const item = data[key];
                const safeKey = escapeHtml(key);
                return `
                    <div class="glass-panel p-4 rounded-xl border border-slate-700/60 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
                        <div class="md:w-1/3">
                            <span class="font-mono text-sky-400 font-bold block">${safeKey}</span>
                            <p class="text-slate-400 text-[11px]">${escapeHtml(item.description || '')}</p>
                        </div>
                        <div class="md:w-1/2">
                            <input type="text" id="setting-${safeKey}" value="${escapeHtml(item.value || '')}" class="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-sky-500 font-mono text-xs">
                        </div>
                    </div>
                `;
            }).join('');
        }

        const integPanel = document.getElementById('integrations-panel');
        if (integPanel) {
            let integ = { gemini_api_key: { configured: false, masked: '' }, google_tts_model: '', google_image_model: '', google_use_imagen: false, note: '' };
            if (integRes && integRes.ok) integ = await integRes.json();
            integPanel.innerHTML = `
                <div class="glass-panel p-5 rounded-2xl border border-sky-500/20 bg-sky-500/5 space-y-4">
                    <div class="flex items-start justify-between gap-4">
                        <div>
                            <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2"><i class="fa-solid fa-key text-amber-400"></i><span>مفاتيح الربط والخدمات</span></h3>
                            <p class="text-[11px] text-slate-400 mt-1">${escapeHtml(integ.note || '')}</p>
                        </div>
                        <span class="text-[11px] px-2.5 py-1 rounded-full ${integ.gemini_api_key?.configured ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'bg-amber-500/15 text-amber-300 border border-amber-500/30'} font-bold">${integ.gemini_api_key?.configured ? 'Gemini: مهيأ' : 'Gemini: غير مهيأ'}</span>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        <label class="block md:col-span-2">
                            <span class="block text-slate-300 font-bold mb-1">GEMINI_API_KEY ${integ.gemini_api_key?.masked ? `<span class="text-slate-500 font-mono">(${escapeHtml(integ.gemini_api_key.masked)})</span>` : ''}</span>
                            <input type="password" id="integration-gemini-key" placeholder="الصق مفتاح Google Gemini API هنا" class="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-sky-500 font-mono">
                            <span class="block text-[11px] text-slate-500 mt-1">اتركه فارغًا إذا لا تريد تغييره عند الحفظ. مطلوب لأصوات/صور Google، بينما يعمل الصوت بديل Edge TTS بدون مفتاح.</span>
                        </label>
                        <label class="block">
                            <span class="block text-slate-300 font-bold mb-1">GOOGLE_TTS_MODEL</span>
                            <input type="text" id="integration-tts-model" value="${escapeHtml(integ.google_tts_model || 'gemini-2.5-flash-preview-tts')}" class="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-sky-500 font-mono">
                        </label>
                        <label class="block">
                            <span class="block text-slate-300 font-bold mb-1">GOOGLE_IMAGE_MODEL (اختياري)</span>
                            <input type="text" id="integration-image-model" value="${escapeHtml(integ.google_image_model || '')}" placeholder="مثال: imagen-4.0-generate-001" class="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-sky-500 font-mono">
                        </label>
                        <label class="flex items-center gap-2 md:col-span-2 text-slate-300">
                            <input type="checkbox" id="integration-use-imagen" ${integ.google_use_imagen ? 'checked' : ''} class="rounded border-slate-600 bg-slate-900">
                            <span>استخدام Google Imagen لتوليد الصور عند تهيئته (GOOGLE_USE_IMAGEN)</span>
                        </label>
                    </div>
                    <div class="flex items-center gap-2">
                        <button onclick="saveIntegrationKeys()" class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition"><i class="fa-solid fa-key ml-1"></i>حفظ مفتاح/إعدادات الربط</button>
                        <button onclick="loadSettings()" class="px-4 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-slate-100 font-bold text-xs transition">تحديث الحالة</button>
                    </div>
                </div>
            `;
        }
    } catch (err) {
        console.error('Error loading settings:', err);
    }
}

async function saveIntegrationKeys() {
    const geminiInput = document.getElementById('integration-gemini-key');
    const payload = {
        google_tts_model: document.getElementById('integration-tts-model')?.value || '',
        google_image_model: document.getElementById('integration-image-model')?.value || '',
        google_use_imagen: !!document.getElementById('integration-use-imagen')?.checked
    };
    if (geminiInput && geminiInput.value.trim()) payload.gemini_api_key = geminiInput.value.trim();
    try {
        const res = await apiFetch('/api/integrations/keys', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok || !data.success) throw new Error(data.detail || 'تعذر حفظ المفاتيح');
        if (geminiInput) geminiInput.value = '';
        showToast('تم حفظ إعدادات الربط وتطبيقها فورًا.', 'success');
        await loadSettings();
        await loadOverview();
    } catch (err) {
        showToast(`خطأ في حفظ الربط: ${err.message}`, 'error');
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
        const res = await apiFetch('/api/settings', {
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
        const res = await apiFetch('/api/pipeline/run-full-cycle', { method: 'POST' });
        let data;
        try {
            data = await res.json();
        } catch (_) {
            data = { detail: res.statusText || 'تعذر قراءة استجابة الخادم.' };
        }
        if (!res.ok) {
            showToast(`فشلت الدورة (${res.status}): ${data.detail || res.statusText}`, 'error');
            return;
        }
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
    navigator.clipboard.writeText(el.innerText || el.textContent)
        .then(() => showToast('تم النسخ إلى الحافظة!', 'success'))
        .catch(() => showToast('تعذر النسخ؛ تحقق من صلاحية الحافظة في المتصفح.', 'error'));
}
