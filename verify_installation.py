import importlib, sys
print("Python", sys.version.split()[0])
libs = ["pandas", "numpy", "scipy", "sklearn", "xgboost", "lightgbm", "mlxtend",
        "matplotlib", "seaborn", "sqlalchemy", "pyodbc", "dotenv", "jupyterlab"]
faltan = []
for l in libs:
    try:
        m = importlib.import_module(l)
        print(f"✅ {l:12s}", getattr(m, "__version__", ""))
    except Exception:
        print(f"❌ {l:12s} NO instalada"); faltan.append(l)
print("\n🎉 Todo listo" if not faltan else f"\n⚠ Faltan: {faltan}  -> pip install -r requirements.txt")
