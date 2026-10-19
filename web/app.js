// ==========================================================================
// K-RIPPER - LOGICA CLIENTE MINIMALISTA Y LIMPIA
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  // Elementos DOM
  const urlInput = document.getElementById('url-input');
  const nameInput = document.getElementById('name-input');
  const btnToggleName = document.getElementById('btn-toggle-name');
  const btnClearAll = document.getElementById('btn-clear-all');
  const btnPaste = document.getElementById('btn-paste');
  const platformChip = document.getElementById('platform-chip');
  const btnFormatVideo = document.getElementById('btn-format-video');
  const btnFormatAudio = document.getElementById('btn-format-audio');
  const btnDownload = document.getElementById('btn-download');
  const btnText = document.getElementById('btn-text');
  const ffmpegStatus = document.getElementById('ffmpeg-status');
  const networkIp = document.getElementById('network-ip');

  // Sección de progreso
  const progressCard = document.getElementById('progress-card');
  const btnCloseProgress = document.getElementById('btn-close-progress');
  const progressMediaTitle = document.getElementById('progress-media-title');
  const progressPercentBadge = document.getElementById('progress-percent-badge');
  const progressFill = document.getElementById('progress-fill');
  const metricSpeed = document.getElementById('metric-speed');
  const metricEta = document.getElementById('metric-eta');
  const metricFolder = document.getElementById('metric-folder');

  // Logs y Toast
  const btnToggleLog = document.getElementById('btn-toggle-log');
  const logContainer = document.getElementById('log-container');
  const logArrow = document.getElementById('log-arrow');
  const logTerminal = document.getElementById('log-terminal');
  const toast = document.getElementById('toast');

  let currentFormat = 'video';
  let eventSource = null;
  let isDownloading = false;

  // 1. Cargar información de red y motor FFmpeg
  async function loadSystemInfo() {
    try {
      const res = await fetch('/api/info');
      const data = await res.json();
      
      if (data.local_ip) {
        networkIp.textContent = `WiFi: http://${data.local_ip}:${data.port}`;
      } else {
        networkIp.textContent = 'Modo Local';
      }

      const dot = ffmpegStatus.querySelector('.status-dot');
      const msg = ffmpegStatus.querySelector('.status-msg');
      if (data.ffmpeg_ready) {
        dot.className = 'status-dot ready';
        msg.textContent = 'FFmpeg activo';
        btnDownload.disabled = false;
      } else {
        dot.className = 'status-dot error';
        msg.textContent = 'FFmpeg no encontrado en ffmpeg/';
        btnDownload.disabled = true;
      }
    } catch (err) {
      networkIp.textContent = 'Desconectado';
    }
  }

  // 2. Detección visual rápida del tipo de URL
  function detectUrlPlatform(url) {
    if (!url || !url.trim()) {
      platformChip.innerHTML = '<span>🔗 Esperando enlace...</span>';
      return;
    }
    const u = url.toLowerCase().trim();
    if (u.includes('.m3u8')) {
      platformChip.innerHTML = '<span>🎬 Streaming HLS (.m3u8)</span>';
    } else if (u.includes('.mpd')) {
      platformChip.innerHTML = '<span>🎬 Streaming DASH (.mpd)</span>';
    } else if (u.includes('youtube.com') || u.includes('youtu.be')) {
      platformChip.innerHTML = '<span>🔴 YouTube</span>';
    } else if (u.includes('tiktok.com')) {
      platformChip.innerHTML = '<span>🎵 TikTok</span>';
    } else if (u.includes('instagram.com')) {
      platformChip.innerHTML = '<span>📸 Instagram</span>';
    } else if (u.includes('twitter.com') || u.includes('x.com')) {
      platformChip.innerHTML = '<span>🐦 Twitter / X</span>';
    } else if (u.includes('facebook.com') || u.includes('fb.watch')) {
      platformChip.innerHTML = '<span>📘 Facebook</span>';
    } else if (u.includes('twitch.tv')) {
      platformChip.innerHTML = '<span>🟣 Twitch</span>';
    } else if (u.includes('soundcloud.com')) {
      platformChip.innerHTML = '<span>🟠 SoundCloud</span>';
    } else if (['streamtape', 'dood', 'filemoon', 'voe.', 'mixdrop', 'ok.ru', 'vidplay', 'mp4upload'].some(h => u.includes(h))) {
      platformChip.innerHTML = '<span>🍿 Servidor de Película</span>';
    } else {
      platformChip.innerHTML = '<span>🌐 Enlace Web Multimedia</span>';
    }
  }

  urlInput.addEventListener('input', (e) => {
    detectUrlPlatform(e.target.value);
  });

  // 3. Botón Pegar Portapapeles
  btnPaste.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        urlInput.value = text.trim();
        detectUrlPlatform(text);
        showToast('Enlace pegado');
        urlInput.focus();
      }
    } catch (e) {
      urlInput.focus();
    }
  });

  // 4. Conmutador de Formato (MP4 / MP3)
  btnFormatVideo.addEventListener('click', () => {
    if (isDownloading) return;
    currentFormat = 'video';
    btnFormatVideo.classList.add('active');
    btnFormatAudio.classList.remove('active');
    metricFolder.textContent = 'videos/';
  });

  btnFormatAudio.addEventListener('click', () => {
    if (isDownloading) return;
    currentFormat = 'audio';
    btnFormatAudio.classList.add('active');
    btnFormatVideo.classList.remove('active');
    metricFolder.textContent = 'musica/';
  });

  // 5. Toggle de Nombre Personalizado
  btnToggleName.addEventListener('click', () => {
    const isShown = nameInput.classList.contains('show');
    if (isShown) {
      nameInput.classList.remove('show');
      btnToggleName.textContent = '+ Nombre personalizado (opcional)';
    } else {
      nameInput.classList.add('show');
      nameInput.focus();
      btnToggleName.textContent = '✕ Ocultar';
    }
  });

  // 6. Conexión de Eventos en Tiempo Real (SSE)
  function connectSSE() {
    if (eventSource) {
      eventSource.close();
    }

    eventSource = new EventSource('/api/events');

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleStreamEvent(data);
      } catch (err) {
        console.error('Error parseando evento:', err);
      }
    };

    eventSource.onerror = () => {
      setTimeout(connectSSE, 3000);
    };
  }

  function handleStreamEvent(data) {
    if (data.type === 'progress') {
      const percent = Math.min(100, Math.max(0, data.percent || 0));
      progressFill.style.width = `${percent.toFixed(1)}%`;
      progressPercentBadge.textContent = `${percent.toFixed(1)}%`;
      metricSpeed.textContent = data.speed || '--';
      metricEta.textContent = data.eta || '--';
      if (data.title) {
        progressMediaTitle.textContent = data.title;
      }
    } else if (data.type === 'finished_video') {
      addLog(`✅ Archivo completado: ${data.title}`, 'success');
    } else if (data.type === 'log') {
      addLog(data.message);
    } else if (data.type === 'status') {
      if (data.status === 'completed') {
        onDownloadFinished(true, '¡Descarga completada!');
      } else if (data.status === 'error') {
        onDownloadFinished(false, data.message || 'Error en la descarga');
      }
    }
  }

  function addLog(message, type = '') {
    const line = document.createElement('div');
    line.className = `log-entry ${type}`;
    line.textContent = message;
    logTerminal.appendChild(line);
    logTerminal.scrollTop = logTerminal.scrollHeight;
  }

  // 7. Iniciar Descarga
  btnDownload.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    const customName = nameInput.value.trim();

    if (!url) {
      showToast('Por favor, ingresa o pega un enlace');
      urlInput.focus();
      return;
    }

    isDownloading = true;
    btnDownload.disabled = true;
    btnText.textContent = 'Descargando...';
    
    // Mostrar progreso
    progressCard.style.display = 'flex';
    progressFill.style.width = '0%';
    progressPercentBadge.textContent = '0%';
    metricSpeed.textContent = '--';
    metricEta.textContent = '--';
    progressMediaTitle.textContent = customName || 'Iniciando conexión con el servidor...';

    addLog(`🚀 Procesando enlace: ${url}`, 'info');

    try {
      const response = await fetch('/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: url,
          format: currentFormat,
          custom_name: customName
        })
      });

      const resData = await response.json();
      if (!response.ok) {
        throw new Error(resData.error || 'Error al iniciar');
      }
    } catch (err) {
      onDownloadFinished(false, err.message);
    }
  });

  // 8. Finalización de la Descarga
  function onDownloadFinished(success, message) {
    isDownloading = false;
    btnDownload.disabled = false;
    btnText.textContent = 'Descargar';

    if (success) {
      progressFill.style.width = '100%';
      progressPercentBadge.textContent = '100%';
      showToast('🎉 ' + message);
      
      // Limpiar automáticamente el input de enlace y nombre como pidió el usuario
      urlInput.value = '';
      nameInput.value = '';
      detectUrlPlatform('');
    } else {
      showToast('❌ ' + message);
    }
  }

  // 9. Función para Limpiar Todo (URL, Nombre, Progreso y Consola)
  function resetAll() {
    // Limpiar entradas
    urlInput.value = '';
    nameInput.value = '';
    nameInput.classList.remove('show');
    btnToggleName.textContent = '+ Nombre personalizado (opcional)';
    detectUrlPlatform('');

    // Ocultar y resetear barra de progreso
    progressCard.style.display = 'none';
    progressFill.style.width = '0%';
    progressPercentBadge.textContent = '0%';
    progressMediaTitle.textContent = 'Descargando...';
    metricSpeed.textContent = '--';
    metricEta.textContent = '--';

    // Limpiar consola de registro
    logTerminal.innerHTML = '<div class="log-entry info">Listo para descargar. Pega un enlace arriba.</div>';
    logContainer.style.display = 'none';
    logArrow.textContent = '▸';

    // Restaurar botón principal si no está descargando
    if (!isDownloading) {
      btnDownload.disabled = false;
      btnText.textContent = 'Descargar';
    }

    showToast('Todo limpio');
  }

  btnClearAll.addEventListener('click', resetAll);
  
  if (btnCloseProgress) {
    btnCloseProgress.addEventListener('click', () => {
      progressCard.style.display = 'none';
    });
  }

  // 10. Toggle de Registro
  btnToggleLog.addEventListener('click', () => {
    const isVisible = logContainer.style.display === 'block';
    logContainer.style.display = isVisible ? 'none' : 'block';
    logArrow.textContent = isVisible ? '▸' : '▾';
  });

  // 11. Toast de aviso
  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 3500);
  }

  // Inicializar
  loadSystemInfo();
  connectSSE();
});
