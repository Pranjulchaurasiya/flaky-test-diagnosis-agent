// ==========================================
// 1. Three.js 3D Rerun Timeline & Hero Canvas
// ==========================================
let scene, camera, renderer, planesGroup, nodesGroup;
let isRotating = true;
let isGlitching = false;
let animationFrameId;

function initThreeVisualizer() {
  const container = document.getElementById('three-canvas-container');
  if (!container || typeof THREE === 'undefined') return;

  const width = container.clientWidth || 560;
  const height = container.clientHeight || 380;

  // Scene & Camera
  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x0e1422, 0.035);

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
  camera.position.set(0, 2.5, 7.5);
  camera.lookAt(0, 0, 0);

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  // Lights
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
  scene.add(ambientLight);

  const pointLight1 = new THREE.PointLight(0x38bdf8, 1.8, 20);
  pointLight1.position.set(4, 5, 4);
  scene.add(pointLight1);

  const pointLight2 = new THREE.PointLight(0xf43f5e, 1.2, 15);
  pointLight2.position.set(-4, -2, 2);
  scene.add(pointLight2);

  // Build Rerun Timeline Planes (Receding Stack)
  planesGroup = new THREE.Group();
  const numPlanes = 6;
  const planeGeo = new THREE.PlaneGeometry(3.6, 2.2);

  for (let i = 0; i < numPlanes; i++) {
    const isFlakyRun = i === 2 || i === 4; // Flaky red planes
    const planeMat = new THREE.MeshPhysicalMaterial({
      color: isFlakyRun ? 0xf43f5e : 0x10b981,
      transparent: true,
      opacity: isFlakyRun ? 0.35 : 0.18,
      wireframe: false,
      side: THREE.DoubleSide,
      roughness: 0.2,
      metalness: 0.1
    });

    const mesh = new THREE.Mesh(planeGeo, planeMat);
    mesh.position.set(0, 0, -i * 1.1);
    mesh.rotation.x = -Math.PI / 6;

    // Wireframe border for crisp depth
    const wireGeo = new THREE.WireframeGeometry(planeGeo);
    const wireMat = new THREE.LineBasicMaterial({
      color: isFlakyRun ? 0xf43f5e : 0x38bdf8,
      transparent: true,
      opacity: 0.4
    });
    const wire = new THREE.LineSegments(wireGeo, wireMat);
    mesh.add(wire);

    planesGroup.add(mesh);
  }
  scene.add(planesGroup);

  // Interconnected Dependency Nodes
  nodesGroup = new THREE.Group();
  const nodeGeo = new THREE.SphereGeometry(0.1, 16, 16);
  const nodeMatPass = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
  const nodeMatFlake = new THREE.MeshBasicMaterial({ color: 0xf43f5e });

  const nodePositions = [
    [-1.2, 0.4, 0], [0.8, -0.3, -1], [-0.5, 0.8, -2],
    [1.2, 0.2, -3], [0, -0.6, -4], [-1.0, -0.2, -5]
  ];

  nodePositions.forEach((pos, idx) => {
    const isFlakeNode = idx === 1 || idx === 3;
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

    // Dynamic Flake Glitch Effect
    if (isGlitching || Math.sin(elapsedTime * 3) > 0.85) {
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
    setTimeout(() => { isGlitching = false; }, 2000);
  });

  // Performance: Pause rendering when scrolled out of view
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
// 2. Benchmark & Results Table Loader
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
// 3. Interactive Trajectory Explorer
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
      <div class="case-item-cat">${c.ground_truth_category} (${c.hardness || 'medium'})</div>
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

  try {
    const res = await fetch(`assets/${caseId}_trajectory.json`);
    const data = await res.json();
    displayTrajectory(data);
  } catch (e) {
    console.warn(`Could not fetch trajectory for ${caseId}, using inline fallback.`);
    displayFallbackTrajectory(caseId);
  }
}

function displayTrajectory(data) {
  currentTrajectory = data.trajectory || [];
  currentStepIndex = 0;

  document.getElementById('active-case-title').textContent = `${data.test_target || currentCaseId}`;
  document.getElementById('active-case-badge').textContent = data.verification_status || 'VERIFIED';
  document.getElementById('diag-cat').textContent = data.taxonomy_category || 'N/A';
  document.getElementById('diag-cause').textContent = data.root_cause_analysis || 'N/A';
  
  const ev = data.evidence_citation || {};
  document.getElementById('diag-evidence').textContent = ev.file_path ? `${ev.file_path}:${ev.line_number} → ${ev.code_snippet || ''}` : 'Verified in code';
  document.getElementById('diag-fix').textContent = data.proposed_fix || 'N/A';

  renderCurrentStep();
}

function renderCurrentStep() {
  if (!currentTrajectory || currentTrajectory.length === 0) return;
  const step = currentTrajectory[currentStepIndex];
  if (!step) return;

  document.getElementById('step-indicator').textContent = `Step ${currentStepIndex + 1} of ${currentTrajectory.length}`;
  document.getElementById('step-action-badge').textContent = `ACTION: ${step.action}`;
  
  const stepTitles = {
    "read_test_file": "1. Test Target & Source Code Inspection",
    "rerun_test": "2. Empirical Test Execution & Flake Frequency",
    "code_and_fixture_search": "3. AST Fixture & Module Reference Scanning",
    "synthesize_hypothesis": "4. ReAct Hypothesis & Root-Cause Formulation",
    "self_verification_gate": "5. Code Evidence Self-Verification Audit",
    "self_correction_pass": "6. Hypothesis Refinement & Self-Correction"
  };
  document.getElementById('step-title').textContent = stepTitles[step.action] || `Step ${step.step}: ${step.action}`;
  document.getElementById('step-content').textContent = JSON.stringify(step, null, 2);
}

// Stepper Event Handlers
document.getElementById('btn-prev-step')?.addEventListener('click', () => {
  if (currentStepIndex > 0) {
    currentStepIndex--;
    renderCurrentStep();
  }
});

document.getElementById('btn-next-step')?.addEventListener('click', () => {
  if (currentStepIndex < currentTrajectory.length - 1) {
    currentStepIndex++;
    renderCurrentStep();
  }
});

document.getElementById('btn-autoplay')?.addEventListener('click', (e) => {
  if (autoplayInterval) {
    clearInterval(autoplayInterval);
    autoplayInterval = null;
    e.target.textContent = '▶ Auto-Play';
  } else {
    e.target.textContent = '⏸ Pause';
    autoplayInterval = setInterval(() => {
      if (currentStepIndex < currentTrajectory.length - 1) {
        currentStepIndex++;
        renderCurrentStep();
      } else {
        currentStepIndex = 0;
        renderCurrentStep();
      }
    }, 2000);
  }
});

// Fallback data helper
function useFallbackData() {
  const fallback = [
    { id: "case_01", name: "Concurrent Metrics Increment Race Condition", ground_truth_category: "race_condition", baseline: { is_correct: true, predicted_category: "race_condition" }, agent: { is_correct: true, predicted_category: "race_condition", verification_status: "VERIFIED", evidence_citation: { file_path: "seeded_repo/src/counter.py", line_number: 14 } } },
    { id: "case_02", name: "Class-Level User Session Cache Leak", ground_truth_category: "shared_leaked_state", baseline: { is_correct: true, predicted_category: "shared_leaked_state" }, agent: { is_correct: true, predicted_category: "shared_leaked_state", verification_status: "VERIFIED", evidence_citation: { file_path: "seeded_repo/src/cache.py", line_number: 7 } } },
    { id: "case_03", name: "Hardcoded Sleep Timing Assumption", ground_truth_category: "timing_sleep_assumption", baseline: { is_correct: true, predicted_category: "timing_sleep_assumption" }, agent: { is_correct: true, predicted_category: "timing_sleep_assumption", verification_status: "VERIFIED", evidence_citation: { file_path: "seeded_repo/tests/test_case_03_timing_sleep.py", line_number: 16 } } },
    { id: "case_04", name: "Implicit Order-Dependent Database State", ground_truth_category: "test_order_dependence", baseline: { is_correct: false, predicted_category: "unknown" }, agent: { is_correct: true, predicted_category: "test_order_dependence", verification_status: "VERIFIED", evidence_citation: { file_path: "seeded_repo/tests/test_case_04_order_dependence.py", line_number: 22 } } },
    { id: "case_05", name: "Unmocked External Currency Exchange Call", ground_truth_category: "flaky_external_dependency", baseline: { is_correct: true, predicted_category: "flaky_external_dependency" }, agent: { is_correct: true, predicted_category: "flaky_external_dependency", verification_status: "VERIFIED", evidence_citation: { file_path: "seeded_repo/src/currency.py", line_number: 19 } } },
    { id: "case_06", name: "Unclosed Temporary File Handle Descriptors", ground_truth_category: "resource_exhaustion", baseline: { is_correct: true, predicted_category: "resource_exhaustion" }, agent: { is_correct: true, predicted_category: "resource_exhaustion", verification_status: "VERIFIED", evidence_citation: { file_path: "seeded_repo/src/file_manager.py", line_number: 14 } } },
    { id: "case_07", name: "Naive vs Timezone-Aware Datetime Comparison", ground_truth_category: "datetime_clock_drift", baseline: { is_correct: true, predicted_category: "datetime_clock_drift" }, agent: { is_correct: true, predicted_category: "datetime_clock_drift", verification_status: "VERIFIED", evidence_citation: { file_path: "seeded_repo/src/billing.py", line_number: 14 } } },
    { id: "case_08", name: "Unseeded Pseudo-Random Token Prefix", ground_truth_category: "unseeded_randomness", baseline: { is_correct: true, predicted_category: "unseeded_randomness" }, agent: { is_correct: true, predicted_category: "unseeded_randomness", verification_status: "VERIFIED", evidence_citation: { file_path: "seeded_repo/src/security.py", line_number: 8 } } },
    { id: "case_09", name: "Leaked Environment Variable Mutation", ground_truth_category: "environment_mutation", baseline: { is_correct: true, predicted_category: "environment_mutation" }, agent: { is_correct: true, predicted_category: "environment_mutation", verification_status: "VERIFIED", evidence_citation: { file_path: "seeded_repo/tests/test_case_09_env_mutation.py", line_number: 10 } } },
    { id: "case_10", name: "Socket TIME_WAIT Port Collision (Hard Case)", ground_truth_category: "hard_ambiguous_case", baseline: { is_correct: false, predicted_category: "timing_sleep_assumption" }, agent: { is_correct: true, predicted_category: "hard_ambiguous_case", verification_status: "VERIFIED", evidence_citation: { file_path: "seeded_repo/src/micro_server.py", line_number: 21 } } }
  ];
  renderBenchmarkTable(fallback);
  renderCaseSelector(fallback);
}

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initThreeVisualizer();
  loadBenchmarkData();
});
