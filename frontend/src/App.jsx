import { useState } from 'react';
import { Zap } from 'lucide-react';
import { apiPost } from './services/api';

const getLocalDateTime = () => {
  const date = new Date();
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
};

const initialForm = {
  timestamp: getLocalDateTime(),
  temperature: 20,
  humidity: 60,
  windspeed: 2.5,
  general_diffuse_flows: 120,
  diffuse_flows: 70,
};

const formatNumber = (value) => Number(value).toLocaleString(undefined, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export default function App() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const prediction = await apiPost('/api/predict', {
        timestamp: form.timestamp,
        temperature: Number(form.temperature),
        humidity: Number(form.humidity),
        windspeed: Number(form.windspeed),
        general_diffuse_flows: Number(form.general_diffuse_flows),
        diffuse_flows: Number(form.diffuse_flows),
      });
      setResult(prediction);
    } catch (submitError) {
      setError(submitError.message || 'Prediction request failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800 bg-slate-950/80">
        <nav className="mx-auto flex max-w-7xl items-center px-4 py-4 sm:px-6 lg:px-8" aria-label="Main navigation">
          <a className="flex items-center gap-3 text-white" href="/" aria-label="VoltCast home">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500/20 text-brand-300">
              <Zap aria-hidden="true" className="h-5 w-5" />
            </span>
            <span className="text-sm font-semibold tracking-[0.16em]">VoltCast</span>
          </a>
        </nav>
      </header>

      <main className="flex min-h-[calc(100vh-68px)] items-center justify-center px-4 py-8 sm:px-6 sm:py-12">
        <section className="card-surface w-full max-w-3xl p-5 sm:p-8 lg:p-10">
          <div className="mb-7 sm:mb-9">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-brand-300">
              Forecasting interface
            </p>
            <h1 className="mt-2 text-2xl font-semibold text-white sm:text-3xl">
              Power consumption prediction
            </h1>
          </div>

          <form className="space-y-7" onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 gap-x-5 gap-y-5 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="label" htmlFor="timestamp">Prediction time</label>
                <input
                  id="timestamp"
                  name="timestamp"
                  type="datetime-local"
                  className="field"
                  required
                  value={form.timestamp}
                  onChange={handleInputChange}
                />
              </div>

              <div>
                <label className="label" htmlFor="temperature">Temperature (°C)</label>
                <input
                  id="temperature"
                  name="temperature"
                  type="number"
                  min="0"
                  max="45"
                  step="0.1"
                  className="field"
                  required
                  value={form.temperature}
                  onChange={handleInputChange}
                />
              </div>

              <div>
                <label className="label" htmlFor="humidity">Humidity (%)</label>
                <input
                  id="humidity"
                  name="humidity"
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  className="field"
                  required
                  value={form.humidity}
                  onChange={handleInputChange}
                />
              </div>

              <div>
                <label className="label" htmlFor="windspeed">Wind speed (m/s)</label>
                <input
                  id="windspeed"
                  name="windspeed"
                  type="number"
                  min="0"
                  max="10"
                  step="0.1"
                  className="field"
                  required
                  value={form.windspeed}
                  onChange={handleInputChange}
                />
              </div>

              <div>
                <label className="label" htmlFor="general_diffuse_flows">General diffuse flow</label>
                <input
                  id="general_diffuse_flows"
                  name="general_diffuse_flows"
                  type="number"
                  min="0"
                  max="1200"
                  step="0.1"
                  className="field"
                  required
                  value={form.general_diffuse_flows}
                  onChange={handleInputChange}
                />
              </div>

              <div>
                <label className="label" htmlFor="diffuse_flows">Diffuse flow</label>
                <input
                  id="diffuse_flows"
                  name="diffuse_flows"
                  type="number"
                  min="0"
                  max="1000"
                  step="0.1"
                  className="field"
                  required
                  value={form.diffuse_flows}
                  onChange={handleInputChange}
                />
              </div>
            </div>

            <div className="flex flex-col gap-4 border-t border-slate-800 pt-5 sm:flex-row sm:items-center">
              <button
                type="submit"
                className="w-full rounded-xl bg-brand-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-brand-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-300 disabled:cursor-wait disabled:opacity-60 sm:w-auto"
                disabled={isLoading}
              >
                {isLoading ? 'Predicting...' : 'Predict power consumption'}
              </button>
              <span className="text-center text-sm text-slate-400 sm:text-left">Unit: kW · Zone 1</span>
            </div>

            {error && (
              <p className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200" role="alert">
                {error}
              </p>
            )}

            {result && (
              <output className="block rounded-2xl border border-emerald-500/40 bg-emerald-500/10 p-5 text-center" aria-live="polite">
                <span className="block text-xs font-medium uppercase tracking-[0.18em] text-emerald-200">
                  Predicted consumption
                </span>
                <span className="mt-2 block text-3xl font-semibold text-white sm:text-4xl">
                  {formatNumber(result.predicted_consumption)} {result.unit}
                </span>
              </output>
            )}
          </form>
        </section>
      </main>
    </div>
  );
}
