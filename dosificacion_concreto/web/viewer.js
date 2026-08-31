/* Visor 3D de elementos estructurales (Three.js).
 * Python -> JS: window.setModel({vertices, indices, rebar, grooves, acento?, label?})
 * Ejes: Python usa z como vertical; aqui se mapea a (x, z, y) con Y arriba.
 */
"use strict";
(function () {
  const host = document.getElementById("host");
  const elemLabel = document.getElementById("elem-label");
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xeef0f7);

  const camera = new THREE.PerspectiveCamera(45, 1, 0.05, 500);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  host.appendChild(renderer.domElement);

  // --- luces ---
  scene.add(new THREE.HemisphereLight(0xffffff, 0x9aa0b0, 0.75));
  const sun = new THREE.DirectionalLight(0xffffff, 1.05);
  sun.position.set(6, 12, 8);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.bias = -0.0005;
  const sc = sun.shadow.camera;
  sc.near = 0.5; sc.far = 80; sc.left = -20; sc.right = 20; sc.top = 20; sc.bottom = -20;
  scene.add(sun);
  const fill = new THREE.DirectionalLight(0xffffff, 0.35);
  fill.position.set(-8, 6, -6);
  scene.add(fill);

  // --- piso + grilla ---
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(200, 200),
    new THREE.ShadowMaterial({ opacity: 0.22 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);
  const grid = new THREE.GridHelper(60, 60, 0xb9bfcf, 0xd3d8e4);
  grid.position.y = 0.001;
  scene.add(grid);

  const concreteMat = new THREE.MeshStandardMaterial({
    color: 0xbcbcc4, roughness: 0.92, metalness: 0.02,
    flatShading: true, side: THREE.DoubleSide,
  });
  const rebarMat = new THREE.MeshStandardMaterial({
    color: 0xb06a2e, roughness: 0.55, metalness: 0.35,
  });
  const wireMat = new THREE.MeshStandardMaterial({
    color: 0xbcbcc4, roughness: 0.92, metalness: 0.02,
    flatShading: true, side: THREE.DoubleSide,
    wireframe: true,
  });

  let modelGroup = new THREE.Group();
  scene.add(modelGroup);

  // --- camara y orbita ---
  const target = new THREE.Vector3(0, 1, 0);
  let radius = 10, theta = 0.9, phi = 1.05;
  let defaultRadius = 10, defaultTheta = 0.9, defaultPhi = 1.05;

  function updateCam() {
    phi = Math.max(0.18, Math.min(1.52, phi));
    radius = Math.max(1.2, Math.min(120, radius));
    camera.position.set(
      target.x + radius * Math.sin(phi) * Math.cos(theta),
      target.y + radius * Math.cos(phi),
      target.z + radius * Math.sin(phi) * Math.sin(theta)
    );
    camera.lookAt(target);
  }

  let dragging = false, lx = 0, ly = 0;
  renderer.domElement.addEventListener("mousedown", (e) => {
    dragging = true; lx = e.clientX; ly = e.clientY;
  });
  window.addEventListener("mouseup", () => { dragging = false; });
  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    theta -= (e.clientX - lx) * 0.01;
    phi -= (e.clientY - ly) * 0.01;
    lx = e.clientX; ly = e.clientY;
    updateCam();
  });
  renderer.domElement.addEventListener("wheel", (e) => {
    e.preventDefault();
    radius *= (e.deltaY > 0 ? 1.1 : 0.9);
    updateCam();
  }, { passive: false });

  // --- soporte tactil ---
  let lastTouchDist = 0;
  renderer.domElement.addEventListener("touchstart", (e) => {
    if (e.touches.length === 1) {
      dragging = true; lx = e.touches[0].clientX; ly = e.touches[0].clientY;
    } else if (e.touches.length === 2) {
      dragging = false;
      lastTouchDist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
    }
    e.preventDefault();
  }, { passive: false });
  renderer.domElement.addEventListener("touchmove", (e) => {
    if (e.touches.length === 1 && dragging) {
      theta -= (e.touches[0].clientX - lx) * 0.012;
      phi -= (e.touches[0].clientY - ly) * 0.012;
      lx = e.touches[0].clientX; ly = e.touches[0].clientY;
      updateCam();
    } else if (e.touches.length === 2) {
      const dist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      if (lastTouchDist) radius = Math.max(1.2, Math.min(120, radius * lastTouchDist / dist));
      lastTouchDist = dist;
      updateCam();
    }
    e.preventDefault();
  }, { passive: false });
  renderer.domElement.addEventListener("touchend", () => {
    dragging = false; lastTouchDist = 0;
  });

  // --- auto-rotate ---
  let autoRotate = false;
  const btnRotate = document.getElementById("btn-rotate");
  btnRotate.addEventListener("click", () => {
    autoRotate = !autoRotate;
    btnRotate.classList.toggle("active", autoRotate);
  });

  // --- wireframe toggle ---
  let wireframe = false;
  const btnWire = document.getElementById("btn-wire");
  btnWire.addEventListener("click", () => {
    wireframe = !wireframe;
    btnWire.classList.toggle("active", wireframe);
    modelGroup.traverse((obj) => {
      if (obj.isMesh && obj.material === concreteMat) {
        obj.material = wireframe ? wireMat : concreteMat;
      } else if (obj.isMesh && obj.material === wireMat) {
        obj.material = wireframe ? wireMat : concreteMat;
      }
    });
  });

  // --- reset camara ---
  document.getElementById("btn-reset").addEventListener("click", () => {
    radius = defaultRadius; theta = defaultTheta; phi = defaultPhi;
    updateCam();
  });

  // --- helper barra de acero ---
  function bar(a, b) {
    const dir = new THREE.Vector3().subVectors(b, a);
    const len = dir.length();
    if (len < 1e-4) return null;
    const g = new THREE.CylinderGeometry(0.011, 0.011, len, 8);
    const m = new THREE.Mesh(g, rebarMat);
    m.castShadow = true;
    m.position.copy(a).addScaledVector(dir, 0.5);
    m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
    return m;
  }

  // Python (x,y,z) -> Three (x, z, y)
  function V(px, py, pz) { return new THREE.Vector3(px, pz, py); }

  // Mezcla un color hex con gris base para tinte de concreto (t=0.10)
  function _tintConcreto(hexAccento) {
    if (!hexAccento || hexAccento.length < 7) return;
    try {
      const ar = parseInt(hexAccento.slice(1, 3), 16) / 255;
      const ag = parseInt(hexAccento.slice(3, 5), 16) / 255;
      const ab = parseInt(hexAccento.slice(5, 7), 16) / 255;
      const t = 0.09;
      const br = 0.737, bg = 0.737, bb = 0.769; // #bcbcc4
      concreteMat.color.setRGB(
        br + (ar - br) * t,
        bg + (ag - bg) * t,
        bb + (ab - bb) * t
      );
      wireMat.color.copy(concreteMat.color);
    } catch (_) {}
  }

  window.setModel = function (data) {
    scene.remove(modelGroup);
    modelGroup = new THREE.Group();

    // Color de concreto segun tipo de elemento
    if (data.acento) _tintConcreto(data.acento);
    else concreteMat.color.setHex(0xbcbcc4);

    // Etiqueta de elemento
    if (data.label) {
      elemLabel.textContent = data.label;
      elemLabel.style.display = "block";
    } else {
      elemLabel.style.display = "none";
    }

    const pos = [];
    const v = data.vertices || [];
    for (let i = 0; i < v.length; i += 3) { pos.push(v[i], v[i + 2], v[i + 1]); }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    if (data.indices && data.indices.length) g.setIndex(data.indices);
    g.computeVertexNormals();
    const mesh = new THREE.Mesh(g, wireframe ? wireMat : concreteMat);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    modelGroup.add(mesh);

    (data.rebar || []).forEach((s) => {
      const m = bar(V(s[0], s[1], s[2]), V(s[3], s[4], s[5]));
      if (m) modelGroup.add(m);
    });

    if (data.grooves && data.grooves.length) {
      const gp = [];
      data.grooves.forEach((s) => { gp.push(s[0], s[2], s[1], s[3], s[5], s[4]); });
      const lg = new THREE.BufferGeometry();
      lg.setAttribute("position", new THREE.Float32BufferAttribute(gp, 3));
      modelGroup.add(new THREE.LineSegments(lg, new THREE.LineBasicMaterial({ color: 0x7c7c86 })));
    }

    scene.add(modelGroup);

    // Centrar en XZ, apoyar en piso, encuadrar camara
    const box = new THREE.Box3().setFromObject(mesh);
    const size = new THREE.Vector3(); box.getSize(size);
    const center = new THREE.Vector3(); box.getCenter(center);
    modelGroup.position.set(-center.x, -box.min.y, -center.z);
    target.set(0, size.y / 2, 0);
    const rad = Math.hypot(size.x, size.y, size.z) * 0.5 || 1;
    radius = rad / Math.sin((camera.fov * Math.PI / 180) / 2) * 0.92 + 0.6;
    defaultRadius = radius; defaultTheta = theta; defaultPhi = phi;
    updateCam();
  };

  function resize() {
    const w = host.clientWidth || 300, h = host.clientHeight || 300;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  window.addEventListener("resize", resize);
  resize();
  updateCam();

  (function loop() {
    requestAnimationFrame(loop);
    if (autoRotate) { theta += 0.007; updateCam(); }
    renderer.render(scene, camera);
  })();

  window._viewerReady = true;
})();
