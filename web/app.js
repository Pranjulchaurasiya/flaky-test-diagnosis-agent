// ==========================================
// 1. Dual Theme Toggle Controller
// ==========================================
function initThemeController() {
  const toggleBtn = document.getElementById('theme-toggle');
  if (!toggleBtn) return;

  function updateThemeUI(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('flakyguard:theme', theme);
    if (scene && scene.fog) {
      const fogColor = theme === 'light' ? 0xf1f5f9 : 0x0a0f1c;
      scene.fog.color.setHex(fogColor);
    }
  }

  toggleBtn.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    updateThemeUI(next);
  });
}

// ==========================================
// 2. Section Rail Observer (Brace-inspired)
// ==========================================
function initSectionRail() {
  const railStep = document.getElementById('rail-step');
  const railLabel = document.getElementById('rail-label');
  if (!railStep || !railLabel) return;

  const sections = document.querySelectorAll('section[data-section-name]');
  const total = sections.length;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const secName = entry.target.getAttribute('data-section-name') || 'overview';
        let secIdx = 1;
        sections.forEach((s, idx) => {
          if (s === entry.target) secIdx = idx + 1;
        });
        railStep.textContent = `[0${secIdx}/0${total}]`;
        railLabel.textContent = `› ${secName}`;
      }
    });
  }, { threshold: 0.35 });

  sections.forEach(sec => observer.observe(sec));
}

// ==========================================
// 3. Three.js 3D Rerun Instability Canvas
// ==========================================
let scene, camera, renderer, planesGroup, nodesGroup;
let isRotating = true;
let isGlitching = false;
let animationFrameId;

function initThreeVisualizer() {
  const container = document.getElementById('three-canvas-container');
  if (!container || typeof THREE === 'undefined') return;

  const width = container.clientWidth || 560;
  const height = container.clientHeight || 360;

  const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
  const fogColor = currentTheme === 'light' ? 0xf1f5f9 : 0x0a0f1c;

  // Scene & Camera
  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(fogColor, 0.04);

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
  camera.position.set(0, 2.5, 7.5);
  camera.lookAt(0, 0, 0);

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  // Lights
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
  scene.add(ambientLight);

  const pointLight1 = new THREE.PointLight(0x0284c7, 2, 20);
  pointLight1.position.set(4, 5, 4);
  scene.add(pointLight1);

  const pointLight2 = new THREE.PointLight(0xf43f5e, 1.5, 15);
  pointLight2.position.set(-4, -2, 2);
  scene.add(pointLight2);

  // Build Rerun Timeline Planes (Receding Stack)
  planesGroup = new THREE.Group();
  const numPlanes = 6;
  const planeGeo = new THREE.PlaneGeometry(3.6, 2.2);

  for (let i = 0; i < numPlanes; i++) {
    const isFlakyRun = i === 2 || i === 4; // Simulated flaky divergence
    const planeMat = new THREE.MeshPhysicalMaterial({
      color: isFlakyRun ? 0xf43f5e : 0x059669,
      transparent: true,
      opacity: isFlakyRun ? 0.4 : 0.2,
      wireframe: false,
      side: THREE.DoubleSide,
      roughness: 0.2,
      metalness: 0.1
    });

    const mesh = new THREE.Mesh(planeGeo, planeMat);
    mesh.position.set(0, 0, -i * 1.1);
    planesGroup.add(mesh);

    // Wireframe border for crisp technical precision
    const wireMat = new THREE.LineBasicMaterial({
      color: isFlakyRun ? 0xfb7185 : 0x34d399,
      transparent: true,
      opacity: 0.6
    });
    const wireGeo = new THREE.WireframeGeometry(planeGeo);
    const wireframe = new THREE.LineSegments(wireGeo, wireMat);
    wireframe.position.set(0, 0, -i * 1.1);
    planesGroup.add(wireframe);
  }

  scene.add(planesGroup);

  // Floating Diagnostic Telemetry Nodes
  nodesGroup = new THREE.Group();
  const nodeGeo = new THREE.SphereGeometry(0.08, 16, 16);
  const nodeMatPass = new THREE.MeshBasicMaterial({ color: 0x34d399 });
  const nodeMatFlake = new THREE.MeshBasicMaterial({ color: 0xfb7185 });

  const nodePositions = [
    [-1.2, 0.6, 0], [0.8, -0.4, 0],
    [-0.5, 0.2, -1.1], [1.1, 0.5, -1.1],
    [-0.9, -0.7, -2.2], [0.3, 0.8, -2.2],
    [0.7, -0.3, -3.3], [-0.4, 0.5, -3.3],
    [-0.8, 0.4, -4.4], [0.9, -0.6, -4.4],
    [-0.2, -0.3, -5.5], [1.0, 0.4, -5.5]
  ];

  nodePositions.forEach((pos, idx) => {
    const isFlakeNode = idx % 3 === 2;
    const sphere = new THREE.Mesh(nodeGeo, isFlakeNode ? nodeMatFlake : nodeMatPass);
    sphere.position.set(...pos);
    nodesGroup.add(sphere);
  });

  scene.add(nodesGroup);

  // Handle Resize
  window.addEventListener('resize', () => {
    if (!container) return;
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  });

  // Animation Loop
  let clock = new THREE.Clock();
  function animate() {
    animationFrameId = requestAnimationFrame(animate);
    const elapsedTime = clock.getElapsedTime();

    if (isRotating) {
      planesGroup.rotation.y = Math.sin(elapsedTime * 0.4) * 0.15;
      planesGroup.rotation.x = Math.sin(elapsedTime * 0.2) * 0.08 - 0.2;
      nodesGroup.rotation.y = planesGroup.rotation.y;
    }

    // Flake Glitch Effect
    if (isGlitching || Math.sin(elapsedTime * 3) > 0.88) {
      const flakePlane = planesGroup.children[2];
      if (flakePlane) {
        flakePlane.position.x = Math.sin(elapsedTime * 20) * 0.08;
      }
    }

    renderer.render(scene, camera);
  }
  animate();

  // Controls Wiring
  document.getElementById('btn-tilt-toggle')?.addEventListener('click', () => {
    isRotating = !isRotating;
  });

  document.getElementById('btn-glitch-toggle')?.addEventListener('click', () => {
    isGlitching = true;
    setTimeout(() => { isGlitching = false; }, 2200);
  });

  // Pause rendering when scrolled out of view
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) {
        cancelAnimationFrame(animationFrameId);
      } else {
        animate();
      }
    });
  }, { threshold: 0.1 });
  observer.observe(container);
}

// ==========================================
// 4. Benchmark & Results Table Loader
// ==========================================
let benchmarkResults = [];
let caseTrajectories = {};

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
      <td class="col-id"><strong>${c.id}</strong></td>
      <td class="col-name"><div class="target-name">${c.name}</div></td>
      <td class="col-cat"><span class="badge-pill">${c.ground_truth_category}</span></td>
      <td class="col-baseline"><span class="badge-pill ${isBaselineCorrect ? 'pass' : 'fail'}">${isBaselineCorrect ? '✅ ' + c.baseline.predicted_category : '❌ ' + (c.baseline?.predicted_category || 'Fail')}</span></td>
      <td class="col-agent"><span class="badge-pill ${isAgentCorrect ? 'pass' : 'fail'}">${isAgentCorrect ? '✅ ' + c.agent.predicted_category : '❌ Fail'}</span></td>
      <td class="col-citation"><code>${citeText}</code></td>
      <td class="col-verification"><span class="badge-pill ${verified ? 'verified' : 'fail'}">${verified ? 'VERIFIED' : 'UNVERIFIED'}</span></td>
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
    badgeEl.className = `case-badge ${isVer ? 'verified' : 'fail'}`;

    // Populate final diagnosis card
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
    case 'run_test_in_isolation': return 'Empirical Test Runner: Isolated Execution';
    case 'run_test_session': return 'Empirical Test Runner: Multi-Run Session Analysis';
    case 'search_code': return 'Code Search: Inspecting Source Implementation';
    case 'inspect_git_blame': return 'Git Inspector: History & Blame Forensics';
    case 'analyze_fixtures': return 'AST Fixture Analyzer: Shared State Audit';
    case 'self_verify': return 'Self-Verification Gate: Code Grounding Audit';
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
    { step: 1, action: "read_test_file", result: { status: "read", lines: 35 } },
    { step: 2, action: "run_test_in_isolation", result: { runs: 5, failures: 3, flake_rate: 0.6 } },
    { step: 3, action: "search_code", result: { matches: 2, file: "src/micro_server.py" } },
    { step: 4, action: "self_verify", result: { verified: true, line: 24 } }
  ];
}

function useFallbackData() {
  benchmarkResults = [
    { id: "case_01", name: "Concurrent Metrics Increment Race Condition", ground_truth_category: "race_condition", baseline: { is_correct: true, predicted_category: "race_condition" }, agent: { is_correct: true, predicted_category: "race_condition", verification_status: "VERIFIED", evidence_citation: { file_path: "seeded_repo/src/counter.py", line_number: 14 } } },
    { id: "case_10", name: "Socket TIME_WAIT Port Collision", ground_truth_category: "hard_ambiguous_case", baseline: { is_correct: true, predicted_category: "hard_ambiguous_case" }, agent: { is_correct: true, predicted_category: "hard_ambiguous_case", verification_status: "VERIFIED", evidence_citation: { file_path: "seeded_repo/src/micro_server.py", line_number: 24 } } }
  ];
  renderBenchmarkTable(benchmarkResults);
  renderCaseSelector(benchmarkResults);
}

// ==========================================
// Initialization on DOM Load
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  initThemeController();
  initSectionRail();
  initThreeVisualizer();
  initStepperControls();
  loadBenchmarkData();
});
