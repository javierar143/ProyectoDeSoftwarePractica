<template>
  <main class="maintenance-page">
    <section class="maintenance-card">
      <div class="icon-container">
        🛠️
      </div>

      <h1>Estamos realizando mejoras</h1>

      <p>
        El sistema se encuentra en mantenimiento temporalmente.
      </p>

      <div>
        <span class="badge">Modo Mantenimiento Activo</span>
      </div>
    </section>
  </main>
</template>

<style scoped>
.maintenance-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  margin: 0;
  padding: 0;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
    'Helvetica Neue', Arial, sans-serif;
  background-color: #f4f7f6;
  color: #2c3e50;
}

.maintenance-card {
  background-color: #ffffff;
  padding: 40px 30px;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
  text-align: center;
  max-width: 480px;
  width: 90%;
  box-sizing: border-box;
  border-top: 5px solid #e67e22;
}

.icon-container {
  font-size: 50px;
  margin-bottom: 20px;
}

h1 {
  font-size: 24px;
  margin-bottom: 15px;
  color: #2c3e50;
  font-weight: 700;
}

p {
  font-size: 16px;
  line-height: 1.6;
  color: #7f8c8d;
  margin: 0;
}

.badge {
  display: inline-block;
  margin-top: 25px;
  padding: 6px 14px;
  background-color: rgba(230, 126, 34, 0.1);
  color: #e67e22;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
</style>