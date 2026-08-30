// ==========================================
// 1. Dual Theme Controller (Brace-inspired)
// ==========================================
function initThemeController() {
  const toggleBtn = document.getElementById('themeToggle');
  const themeLabel = document.getElementById('themeLabel');
  if (!toggleBtn) return;

  function updateThemeUI(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('flakyguard:theme', theme); } catch(e) {}
    if (themeLabel) {
      themeLabel.textContent = theme === 'dark' ? 'light' : 'dark';
    }
    if (scene && scene.fog) {
      const fogColor = theme === 'dark' ? 0x090d13 : 0xeceff4;
      scene.fog.color.setHex(fogColor);
    }
  }

  // Set initial label
  const initialTheme = document.documentElement.getAttribute('data-theme') || 'light';
  if (themeLabel) {
    themeLabel.textContent = initialTheme === 'dark' ? 'light' : 'dark';
  }

  toggleBtn.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    updateThemeUI(next);
  });
}

// ==========================================
// 2. Section Rail Observer
// ==========================================
function initSectionRail() {
  const railStep = document.getElementById('rail-step');
  const railLabel = document.getElementById('rail-label');
  if (!railStep || !railLabel) return;

  const sections = document.querySelectorAll('section[data-sec]');
  const total = sections.length;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const secName = entry.target.getAttribute('data-sec') || 'overview';
        let secIdx = 1;
        sections.forEach((s, idx) => {
          if (s === entry.target) secIdx = idx + 1;
        });
        railStep.textContent = `[0${secIdx}/0${total}]`;
        railLabel.textContent = `› ${secName}`;
      }
    });
  }, { threshold: 0.3 });

  sections.forEach(sec => observer.observe(sec));
}

// ==========================================
// 3. Three.js 3D Depth Stack
// ==========================================
let scene, camera, renderer, planesGroup, nodesGroup;
let isRotating = true;
let isGlitching = false;
let animationFrameId;

function initThreeVisualizer() {
  const container = document.getElementById('three-canvas-container');
  if (!container || typeof THREE === 'undefined') return;

  const width = container.clientWidth || 560;
  const height = container.clientHeight || 350;

  const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
  const fogColor = currentTheme === 'dark' ? 0x090d13 : 0xeceff4;

  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(fogColor, 0.04);

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
  camera.position.set(0, 2.5, 7.5);
  camera.lookAt(0, 0, 0);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
  scene.add(ambientLight);

  const pointLight1 = new THREE.PointLight(0x0284c7, 2, 20);
  pointLight1.position.set(4, 5, 4);
  scene.add(pointLight1);

  const pointLight2 = new THREE.PointLight(0xcf1a10, 1.5, 15);
  pointLight2.position.set(-4, -2, 2);
  scene.add(pointLight2);

  planesGroup = new THREE.Group();
  const numPlanes = 6;
  const planeGeo = new THREE.PlaneGeometry(3.6, 2.2);

  for (let i = 0; i < numPlanes; i++) {
    const isFlakyRun = i === 2 || i === 4;
    const planeMat = new THREE.MeshPhysicalMaterial({
      color: isFlakyRun ? 0xcf1a10 : 0x097043,
      transparent: true,
      opacity: isFlakyRun ? 0.35 : 0.18,
      side: THREE.DoubleSide,
      roughness: 0.2
    });

    const mesh = new THREE.Mesh(planeGeo, planeMat);
    mesh.position.set(0, 0, -i * 1.1);
    planesGroup.add(mesh);

    const wireMat = new THREE.LineBasicMaterial({
      color: isFlakyRun ? 0xff3b30 : 0x2fe08a,
      transparent: true,
      opacity: 0.55
    });
    const wireGeo = new THREE.WireframeGeometry(planeGeo);
    const wireframe = new THREE.LineSegments(wireGeo, wireMat);
    wireframe.position.set(0, 0, -i * 1.1);
    planesGroup.add(wireframe);
  }

  scene.add(planesGroup);

  nodesGroup = new THREE.Group();
  const nodeGeo = new THREE.SphereGeometry(0.08, 16, 16);
  const nodeMatPass = new THREE.MeshBasicMaterial({ color: 0x097043 });
  const nodeMatFlake = new THREE.MeshBasicMaterial({ color: 0xcf1a10 });

  const nodePositions = [
    [-1.2, 0.6, 0], [0.8, -0.4, 0],
    [-0.5, 0.2, -1.1], [1.1, 0.5, -1.1],
    [-0.9, -0.7, -2.2], [0.3, 0.8, -2.2],
    [0.7, -0.3, -3.3], [-0.4, 0.5, -3.3],
    [-0.8, 0.4, -4.4], [0.9, -0.6, -4.4]
  ];

  nodePositions.forEach((pos, idx) => {
    const isFlakeNode = idx % 3 === 2;
    const sphere = new THREE.Mesh(nodeGeo, isFlakeNode ? nodeMatFlake : nodeMatPass);
    sphere.position.set(...pos);
    nodesGroup.add(sphere);
  });

  scene.add(nodesGroup);

  window.addEventListener('resize', () => {
    if (!container) return;
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  });

  let clock = new THREE.Clock();
  function animate() {
    animationFrameId = requestAnimationFrame(animate);
    const elapsedTime = clock.getElapsedTime();

    if (isRotating) {
      planesGroup.rotation.y = Math.sin(elapsedTime * 0.4) * 0.15;
      planesGroup.rotation.x = Math.sin(elapsedTime * 0.2) * 0.08 - 0.2;
      nodesGroup.rotation.y = planesGroup.rotation.y;
    }

    if (isGlitching || Math.sin(elapsedTime * 3) > 0.88) {
      const flakePlane = planesGroup.children[2];
      if (flakePlane) {
        flakePlane.position.x = Math.sin(elapsedTime * 20) * 0.08;
      }
    }

    renderer.render(scene, camera);
  }
  animate();

  document.getElementById('btn-tilt-toggle')?.addEventListener('click', () => {
    isRotating = !isRotating;
  });

  document.getElementById('btn-glitch-toggle')?.addEventListener('click', () => {
    isGlitching = true;
    setTimeout(() => { isGlitching = false; }, 2200);
  });
}

// ==========================================
// 4. Benchmark Table Loader
// ==========================================
let benchmarkResults = [];

async function loadBenchmarkData() {
  try {
    const res = await fetch('assets/results.json');
    const data = await res.json();
    benchmarkResults = data.results || [];
    renderBenchmarkTable(benchmarkResults);
    renderCaseSelector(benchmarkResults);
    if (benchmarkResults.length > 0) {
      loadCaseTrajectory(benchmarkResults[0].id);
    }
  } catch (err) {
    console.warn('Using embedded fallback benchmark data:', err);
    useFallbackData();
  }
}

function renderBenchmarkTable(results) {
  const tbody = document.getElementById('table-body');
  if (!tbody) return;
  tbody.innerHTML = '';

  results.forEach(c => {
    const tr = document.createElement('tr');
    const isBaselineCorrect = c.baseline?.is_correct;
    const isAgentCorrect = c.agent?.is_correct;
    const verified = c.agent?.verification_status === 'VERIFIED';
    const evidence = c.agent?.evidence_citation;
    const citeText = evidence?.file_path ? `${evidence.file_path}:${evidence.line_number}` : 'N/A';

    tr.innerHTML = `
      <td><strong>${c.id}</strong></td>
      <td><b>${c.name}</b></td>
      <td><span class="badge">${c.ground_truth_category}</span></td>
      <td><span class="badge ${isBaselineCorrect ? 'badge--pass' : 'badge--fail'}">${isBaselineCorrect ? '✅ ' + c.baseline.predicted_category : '❌ ' + (c.baseline?.predicted_category || 'Fail')}</span></td>
      <td><span class="badge ${isAgentCorrect ? 'badge--pass' : 'badge--fail'}">${isAgentCorrect ? '✅ ' + c.agent.predicted_category : '❌ Fail'}</span></td>
      <td><code>${citeText}</code></td>
      <td><span class="badge ${verified ? 'badge--ver' : 'badge--fail'}">${verified ? 'VERIFIED' : 'UNVERIFIED'}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// ==========================================
// 5. Interactive Forensic Trajectory Lab
// ==========================================
let currentCaseId = 'case_01';
let currentTrajectory = [];
let currentStepIndex = 0;
let autoplayInterval = null;

function renderCaseSelector(results) {
  const list = document.getElementById('case-list');
  if (!list) return;
  list.innerHTML = '';

  results.forEach((c, idx) => {
    const item = document.createElement('div');
    item.className = `case-item ${idx === 0 ? 'active' : ''}`;
    item.dataset.caseId = c.id;
    item.innerHTML = `
      <div class="case-item-title">${c.id}: ${c.name}</div>
      <div class="case-item-meta">${c.ground_truth_category} (${c.hardness || 'medium'})</div>
    `;
    item.addEventListener('click', () => {
      document.querySelectorAll('.case-item').forEach(el => el.classList.remove('active'));
      item.classList.add('active');
      loadCaseTrajectory(c.id);
    });
    list.appendChild(item);
  });
}

async function loadCaseTrajectory(caseId) {
  currentCaseId = caseId;
  currentStepIndex = 0;
  clearInterval(autoplayInterval);
  document.getElementById('btn-autoplay')?.classList.remove('active');

  const activeResult = benchmarkResults.find(r => r.id === caseId);
  const headlineEl = document.getElementById('active-case-title');
  const badgeEl = document.getElementById('active-case-badge');

  if (activeResult) {
    headlineEl.textContent = `${activeResult.id}: ${activeResult.name}`;
    const isVer = activeResult.agent?.verification_status === 'VERIFIED';
    badgeEl.textContent = isVer ? 'VERIFIED' : 'UNVERIFIED';
    badgeEl.className = `badge ${isVer ? 'badge--ver' : 'badge--fail'}`;

    document.getElementById('diag-cat').textContent = activeResult.ground_truth_category || 'N/A';
    document.getElementById('diag-cause').textContent = activeResult.agent?.root_cause || 'Root cause under investigation.';
    
    const cite = activeResult.agent?.evidence_citation;
    if (cite && cite.file_path) {
      const snip = cite.snippet ? ` → "${cite.snippet}"` : '';
      document.getElementById('diag-evidence').textContent = `${cite.file_path}:${cite.line_number}${snip}`;
    } else {
      document.getElementById('diag-evidence').textContent = 'N/A';
    }
    document.getElementById('diag-fix').textContent = activeResult.agent?.proposed_fix || 'No fix patch proposed.';
  }

  try {
    const res = await fetch(`assets/${caseId}_trajectory.json`);
    const data = await res.json();
    currentTrajectory = data.trajectory || data.steps || [];
    renderStep(currentStepIndex);
  } catch (err) {
    console.warn(`Could not load trajectory for ${caseId}:`, err);
    currentTrajectory = getFallbackTrajectory(caseId);
    renderStep(currentStepIndex);
  }
}

function renderStep(idx) {
  if (!currentTrajectory || currentTrajectory.length === 0) return;
  const step = currentTrajectory[idx] || currentTrajectory[0];

  const indicator = document.getElementById('step-indicator');
  const actionBadge = document.getElementById('step-action-badge');
  const title = document.getElementById('step-title');
  const content = document.getElementById('step-content');

  indicator.textContent = `Step ${idx + 1} of ${currentTrajectory.length}`;
  actionBadge.textContent = `ACTION: ${step.action || 'investigate'}`;
  title.textContent = `Step ${step.step || idx + 1}: ${formatStepTitle(step.action)}`;
  
  content.textContent = JSON.stringify(step, null, 2);
}

function formatStepTitle(action) {
  switch (action) {
    case 'read_test_file': return 'Initial Test Context & AST Analysis';
    case 'rerun_test': return 'Empirical Multi-Rerun Runner';
    case 'run_test_in_isolation': return 'Isolated Test Execution';
    case 'search_code': return 'Code Search: Implementation Inspection';
    case 'inspect_git_blame': return 'Git Forensics: Blame & Commit Inspection';
    case 'analyze_fixtures': return 'AST Fixture Analyzer';
    case 'self_verify': return 'Code Grounding Self-Verification Gate';
    default: return 'Forensic Investigation Step';
  }
}

function initStepperControls() {
  document.getElementById('btn-prev-step')?.addEventListener('click', () => {
    if (currentStepIndex > 0) {
      currentStepIndex--;
      renderStep(currentStepIndex);
    }
  });

  document.getElementById('btn-next-step')?.addEventListener('click', () => {
    if (currentStepIndex < currentTrajectory.length - 1) {
      currentStepIndex++;
      renderStep(currentStepIndex);
    }
  });

  const autoplayBtn = document.getElementById('btn-autoplay');
  autoplayBtn?.addEventListener('click', () => {
    if (autoplayInterval) {
      clearInterval(autoplayInterval);
      autoplayInterval = null;
      autoplayBtn.classList.remove('active');
      autoplayBtn.textContent = '▶ Auto-Play Steps';
    } else {
      autoplayBtn.classList.add('active');
      autoplayBtn.textContent = '⏸ Pause';
      autoplayInterval = setInterval(() => {
        if (currentStepIndex < currentTrajectory.length - 1) {
          currentStepIndex++;
          renderStep(currentStepIndex);
        } else {
          currentStepIndex = 0;
          renderStep(currentStepIndex);
        }
      }, 2500);
    }
  });
}

function getFallbackTrajectory(caseId) {
  return [
    { step: 1, action: "read_test_file", target: "seeded_repo/tests/test.py", result_summary: "Read test file" },
    { step: 2, action: "rerun_test", runs: 3, failures: 3, flake_rate: 1.0 },
    { step: 3, action: "self_verify", verified: true, line: 14 }
  ];
}

function useFallbackData() {
  benchmarkResults = [
    { id: "case_01", name: "Concurrent Metrics Increment Race Condition", ground_truth_category: "race_condition", baseline: { is_correct: true, predicted_category: "race_condition" }, agent: { is_correct: true, predicted_category: "race_condition", verification_status: "VERIFIED", evidence_citation: { file_path: "seeded_repo/src/counter.py", line_number: 14 } } }
  ];
  renderBenchmarkTable(benchmarkResults);
  renderCaseSelector(benchmarkResults);
}

document.addEventListener('DOMContentLoaded', () => {
  initThemeController();
  initSectionRail();
  initThreeVisualizer();
  initStepperControls();
  loadBenchmarkData();
});
