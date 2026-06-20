import { useEffect, useRef, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import { PageShell } from '../components/UI';
import { api } from '../lib/api';

export default function AttendancePage() {
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState<{ game_name: string; points_awarded: number; already_scanned: boolean } | null>(null);
  const [error, setError] = useState('');
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const containerId = 'qr-reader';

  const stopScanner = async () => {
    if (scannerRef.current) {
      try {
        await scannerRef.current.stop();
      } catch { /* already stopped */ }
      scannerRef.current = null;
    }
    setScanning(false);
  };

  const startScanner = async () => {
    setError('');
    setResult(null);
    setScanning(true);

    await new Promise((r) => setTimeout(r, 100));

    try {
      const scanner = new Html5Qrcode(containerId);
      scannerRef.current = scanner;
      await scanner.start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        async (decodedText) => {
          await stopScanner();
          try {
            const res = await api.scanAttendance(decodedText);
            setResult(res);
          } catch (err) {
            setError(err instanceof Error ? err.message : 'Scan failed');
          }
        },
        () => {}
      );
    } catch (err) {
      setScanning(false);
      setError('Camera access denied or unavailable. Try manual entry below.');
    }
  };

  useEffect(() => {
    return () => { stopScanner(); };
  }, []);

  const manualSubmit = async (payload: string) => {
    setError('');
    try {
      const res = await api.scanAttendance(payload);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid code');
    }
  };

  return (
    <PageShell title="Attendance Bonus" backTo="/">
      <p className="text-gray-400 text-sm text-center mb-6">
        Scan the QR code displayed during each game for +4 bonus points. Stackable across all 4 games!
      </p>

      {!scanning && !result && (
        <button
          onClick={startScanner}
          className="w-full touch-target rounded-xl bg-gold text-pitch-dark py-5 text-lg font-bold mb-4 active:scale-98 transition"
        >
          📷 Scan QR Code
        </button>
      )}

      {scanning && (
        <div className="mb-4">
          <div id={containerId} className="rounded-xl overflow-hidden" />
          <button onClick={stopScanner} className="w-full mt-3 text-gray-400 underline text-sm">
            Cancel
          </button>
        </div>
      )}

      {result && (
        <div className={`rounded-xl p-6 text-center ${result.already_scanned ? 'bg-gray-800' : 'bg-pitch-light'}`}>
          {result.already_scanned ? (
            <>
              <p className="text-2xl mb-2">✓</p>
              <p>Already scanned for <strong>{result.game_name}</strong></p>
            </>
          ) : (
            <>
              <p className="text-2xl mb-2">🎉</p>
              <p className="font-bold text-lg">{result.game_name}</p>
              <p className="text-gold text-2xl font-black mt-2">+{result.points_awarded} pts</p>
            </>
          )}
          <button onClick={() => { setResult(null); startScanner(); }} className="mt-4 text-sm underline text-gray-400">
            Scan another
          </button>
        </div>
      )}

      {error && <p className="text-red-400 text-center text-sm mb-4">{error}</p>}

      <div className="mt-6">
        <p className="text-xs text-gray-500 text-center mb-2">Or paste QR payload manually:</p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const input = (e.target as HTMLFormElement).payload as HTMLInputElement;
            manualSubmit(input.value);
          }}
        >
          <input
            name="payload"
            placeholder="wc26-attendance:..."
            className="w-full rounded-xl bg-card border border-pitch-light/40 px-4 py-3 text-sm focus:outline-none focus:border-gold"
          />
        </form>
      </div>
    </PageShell>
  );
}
