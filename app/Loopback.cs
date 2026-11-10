using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;

// Windows shared-mode WASAPI loopback. Stdout contains framed float32 PCM only.
class Loopback {
    [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class Enumerator {}
    [ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IEnum {
        void EnumAudioEndpoints(int flow, uint mask, out IntPtr devices);
        void GetDefaultAudioEndpoint(int flow, int role, out IDevice device);
    }
    [ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IDevice {
        void Activate(ref Guid iid, uint context, IntPtr parameters, [MarshalAs(UnmanagedType.IUnknown)] out object obj);
    }
    [ComImport, Guid("1CB9AD4C-DBFA-4C32-B178-C2F568A703B2"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IAudio {
        void Initialize(int mode, uint flags, long duration, long periodicity, IntPtr format, IntPtr session);
        void GetBufferSize(out uint frames);
        void GetStreamLatency(out long latency);
        void GetCurrentPadding(out uint frames);
        [PreserveSig] int IsFormatSupported(int mode, IntPtr format, out IntPtr closest);
        void GetMixFormat(out IntPtr format);
        void GetDevicePeriod(out long normal, out long minimum);
        void Start(); void Stop(); void Reset(); void SetEventHandle(IntPtr handle);
        void GetService(ref Guid iid, [MarshalAs(UnmanagedType.IUnknown)] out object service);
    }
    [ComImport, Guid("C8ADBD64-E71E-48A0-A4DE-185C395CD317"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface ICapture {
        void GetBuffer(out IntPtr data, out uint frames, out uint flags, out ulong position, out ulong time);
        void ReleaseBuffer(uint frames);
        void GetNextPacketSize(out uint frames);
    }
    [MTAThread]
    static int Main() {
        IAudio audio = null; ICapture capture = null; IDevice device = null;
        IEnum enumerator = null; IntPtr format = IntPtr.Zero;
        try {
            enumerator = (IEnum)new Enumerator();
            enumerator.GetDefaultAudioEndpoint(0, 1, out device);
            Guid audioId = typeof(IAudio).GUID; object obj;
            device.Activate(ref audioId, 23, IntPtr.Zero, out obj); audio = (IAudio)obj;
            audio.GetMixFormat(out format);
            int tag = (ushort)Marshal.ReadInt16(format, 0);
            int channels = (ushort)Marshal.ReadInt16(format, 2);
            int rate = Marshal.ReadInt32(format, 4);
            int align = (ushort)Marshal.ReadInt16(format, 12);
            int bits = (ushort)Marshal.ReadInt16(format, 14);
            if (tag == 65534) tag = Marshal.ReadInt32(format, 24);
            bool floating = tag == 3 && bits == 32;
            if (!floating && !(tag == 1 && (bits == 16 || bits == 24 || bits == 32)))
                throw new Exception("Unsupported mix format: " + tag + "/" + bits);
            // Capture the actual mix format; no third-party driver or Stereo Mix required.
            audio.Initialize(0, 0x20000, 1000000, 0, format, IntPtr.Zero);
            Guid captureId = typeof(ICapture).GUID;
            audio.GetService(ref captureId, out obj); capture = (ICapture)obj;
            int outputChannels = Math.Min(channels, 2);
            Console.Error.WriteLine("WASAPI: " + rate + " Hz, " + channels + " channels, " + bits + " bit; sending " + outputChannels + " channels");
            var writer = new BinaryWriter(Console.OpenStandardOutput());
            writer.Write(new byte[] {76,65,78,49}); writer.Write(rate); writer.Write(outputChannels); writer.Flush();
            audio.Start();
            while (true) {
                uint available; capture.GetNextPacketSize(out available);
                if (available == 0) { Thread.Sleep(5); continue; }
                IntPtr data; uint frames, flags; ulong position, time;
                capture.GetBuffer(out data, out frames, out flags, out position, out time);
                if (frames == 0) continue;
                byte[] output = new byte[checked((int)frames * outputChannels * 4)];
                try {
                    if ((flags & 2) == 0) {
                        byte[] raw = new byte[checked((int)frames * align)];
                        Marshal.Copy(data, raw, 0, raw.Length);
                        for (int f = 0; f < frames; f++) for (int c = 0; c < outputChannels; c++) {
                            int offset = f * align + c * (bits / 8);
                            float value;
                            if (floating) value = BitConverter.ToSingle(raw, offset);
                            else if (bits == 16) value = BitConverter.ToInt16(raw, offset) / 32768f;
                            else if (bits == 32) value = BitConverter.ToInt32(raw, offset) / 2147483648f;
                            else { int v = raw[offset] | (raw[offset+1] << 8) | (raw[offset+2] << 16); value = ((v << 8) >> 8) / 8388608f; }
                            Buffer.BlockCopy(BitConverter.GetBytes(value), 0, output, (f * outputChannels + c) * 4, 4);
                        }
                    }
                } finally { capture.ReleaseBuffer(frames); }
                writer.Write(output.Length); writer.Write(output); writer.Flush();
            }
        } catch (Exception e) { Console.Error.WriteLine("Capture failed: " + e.Message); return 1; }
        finally {
            if (audio != null) { try { audio.Stop(); } catch {} }
            if (format != IntPtr.Zero) Marshal.FreeCoTaskMem(format);
            foreach (object item in new object[] {capture, audio, device, enumerator})
                if (item != null) Marshal.ReleaseComObject(item);
        }
    }
}
