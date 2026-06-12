let selectedFile = null;
let isAnalyzing = false;
let isPlaying = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

function setupEventListeners() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');

    // Click upload area
    uploadZone.addEventListener('click', () => fileInput.click());

    // Drag over
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.style.borderColor = 'var(--primary-blue)';
        uploadZone.style.background = 'var(--light-blue)';
    });

    // Drag leave
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.style.borderColor = 'var(--border-color)';
        uploadZone.style.background = 'transparent';
    });

    // Drop image
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();

        uploadZone.style.borderColor = 'var(--border-color)';
        uploadZone.style.background = 'transparent';

        const file = e.dataTransfer.files[0];

        if (file && file.type.startsWith('image/')) {
            handleFileSelect(file);
        }
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];

        if (file) {
            handleFileSelect(file);
        }
    });
}

// Handle selected image
function handleFileSelect(file) {

    if (file.size > 16 * 1024 * 1024) {
        alert('File size must be less than 16MB');
        return;
    }

    selectedFile = file;

    const reader = new FileReader();

    reader.onload = (e) => {

        const preview = document.getElementById('imagePreview');
        const placeholder = document.getElementById('previewPlaceholder');

        preview.src = e.target.result;
        preview.classList.add('active');

        placeholder.style.display = 'none';

        document.getElementById('analyzeBtn').disabled = false;

        updateStatus('Ready to analyze');
    };

    reader.readAsDataURL(file);
}

// Open file chooser
function chooseImage() {
    document.getElementById('fileInput').click();
}

// MAIN FUNCTION
async function analyzeImage() {

    if (!selectedFile || isAnalyzing) return;

    isAnalyzing = true;

    updateStatus('Analyzing...', 'analyzing');

    const analyzeBtn = document.getElementById('analyzeBtn');

    analyzeBtn.disabled = true;

    try {

        // Create FormData
        const formData = new FormData();

        formData.append('image', selectedFile);

        // Send to Flask backend
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        // Error from backend
        if (!response.ok) {
            throw new Error(data.error || 'Analysis failed');
        }

        // Display results
        displayResults(
            data.caption,
            null,
            data.audio_url
        );

        updateStatus('Complete', 'complete');

    } catch (error) {

        console.error(error);

        updateStatus('Error', 'error');

        alert(error.message || 'Something went wrong');

    } finally {

        isAnalyzing = false;

        analyzeBtn.disabled = false;
    }
}

// Display Results
function displayResults(description, extractedText, audioUrl) {

    document.getElementById('emptyState').style.display = 'none';

    document.getElementById('resultsDisplay').style.display = 'block';

    // Description
    document.getElementById('descriptionText').textContent = description;

    // OCR section
    const ocrSection = document.getElementById('ocrSection');

    if (extractedText) {

        ocrSection.style.display = 'block';

        document.getElementById('ocrText').textContent = extractedText;

    } else {

        ocrSection.style.display = 'none';
    }

    // Save globally
    window.currentAudioUrl = audioUrl;

    window.currentDescription = description;

    window.currentExtractedText = extractedText;
}

// Update status badge
function updateStatus(text, type = 'ready') {

    const badge = document.getElementById('statusBadge');

    badge.textContent = text;

    const colors = {
        ready: {
            bg: '#EFF6FF',
            color: '#3B82F6'
        },

        analyzing: {
            bg: '#FEF3C7',
            color: '#F59E0B'
        },

        complete: {
            bg: '#D1FAE5',
            color: '#10B981'
        },

        error: {
            bg: '#FEE2E2',
            color: '#EF4444'
        }
    };

    const color = colors[type] || colors.ready;

    badge.style.background = color.bg;

    badge.style.color = color.color;
}

// Play / Pause Audio
function toggleAudio() {

    if (!window.currentAudioUrl) {
        alert('No audio available');
        return;
    }

    const playBtn = document.getElementById('playBtn');

    const progressBar = document.getElementById('progressBar');

    // Create audio object
    if (!window.audioElement) {

        window.audioElement = new Audio(
            window.currentAudioUrl + '?t=' + new Date().getTime()
        );

        // Update progress
        window.audioElement.addEventListener('timeupdate', () => {

            const progress =
                (window.audioElement.currentTime /
                    window.audioElement.duration) * 100;

            progressBar.style.width = progress + '%';

            const currentTime = formatTime(
                window.audioElement.currentTime
            );

            document.getElementById('audioTime').textContent = currentTime;
        });

        // Audio ended
        window.audioElement.addEventListener('ended', () => {

            isPlaying = false;

            playBtn.innerHTML = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M8 5v14l11-7L8 5z" fill="currentColor"/>
                </svg>
            `;

            progressBar.style.width = '0%';
        });
    }

    // Pause
    if (isPlaying) {

        window.audioElement.pause();

        playBtn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M8 5v14l11-7L8 5z" fill="currentColor"/>
            </svg>
        `;

    } else {

        // Play
        window.audioElement.play();

        playBtn.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <rect x="6" y="4" width="4" height="16" fill="currentColor"/>
                <rect x="14" y="4" width="4" height="16" fill="currentColor"/>
            </svg>
        `;
    }

    isPlaying = !isPlaying;
}

// Format audio time
function formatTime(seconds) {

    const mins = Math.floor(seconds / 60);

    const secs = Math.floor(seconds % 60);

    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Copy result
function copyResult() {

    let text = window.currentDescription || '';

    if (window.currentExtractedText) {

        text += `\n\nExtracted Text: ${window.currentExtractedText}`;
    }

    navigator.clipboard.writeText(text).then(() => {

        alert('Results copied!');
    });
}

// Download audio
function downloadAudio() {

    if (!window.currentAudioUrl) return;

    const a = document.createElement('a');

    a.href = window.currentAudioUrl;

    a.download = 'audio-description.mp3';

    a.click();
}

// Reset app
function resetApp() {

    selectedFile = null;

    isAnalyzing = false;

    isPlaying = false;

    if (window.audioElement) {

        window.audioElement.pause();

        window.audioElement = null;
    }

    const preview = document.getElementById('imagePreview');

    const placeholder = document.getElementById('previewPlaceholder');

    preview.classList.remove('active');

    preview.src = '';

    placeholder.style.display = 'block';

    document.getElementById('emptyState').style.display = 'block';

    document.getElementById('resultsDisplay').style.display = 'none';

    document.getElementById('analyzeBtn').disabled = true;

    document.getElementById('fileInput').value = '';

    updateStatus('Ready');
}

// Scroll to app
function scrollToApp() {

    document.getElementById('app').scrollIntoView({
        behavior: 'smooth'
    });
}

// Demo button
function playDemo() {

    alert('Demo feature coming soon');
}