import com.winlator.studio.MinidumpDecoder;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Random;

public class DumpTest {
    static int failures = 0;
    static void check(boolean ok, String what) {
        System.out.println((ok ? "PASS " : "FAIL ") + what);
        if (!ok) failures++;
    }
    public static void main(String[] args) throws Exception {
        // args[0]: Breakpad's src/processor/testdata/minidump2.dmp (a real Windows crash dump), or "none".
        // Breakpad's minidump_stackwalk reports for it: EXCEPTION_ACCESS_VIOLATION_WRITE at 0x45, eip 0x0040429e in test_app.exe.
        byte[] real = args[0].equals("none") ? new byte[0] : Files.readAllBytes(Paths.get(args[0]));
        if (real.length > 0) {
            String r = MinidumpDecoder.decode(ByteBuffer.wrap(real));
            System.out.println("--- breakpad minidump2.dmp ---\n" + r);
            check(r != null && r.contains("Exception 0xC0000005 (access violation: write to 0x45)"), "real dump: exception + write address");
            check(r != null && r.contains("= test_app.exe+0x429E"), "real dump: faulting module + offset");
            check(r != null && r.contains("Modules: 13 (first: test_app.exe)"), "real dump: module list");
        }
        else System.out.println("(real dump not available, skipped)");

        byte[] synth = Files.readAllBytes(Paths.get(args[1]));
        String s = MinidumpDecoder.decode(ByteBuffer.wrap(synth));
        System.out.println("--- synthetic x64 dump ---\n" + s);
        check(s != null && s.contains("Exception 0xC0000005 (access violation: write to 0x10) in thread 0x24c"), "x64 dump: exception");
        check(s != null && s.contains("At 0x0000000140123456 = RobloxStudioBeta.exe+0x123456  (C:\\Program Files\\Roblox Studio\\RobloxStudioBeta.exe)"), "x64 dump: module + offset");

        check(MinidumpDecoder.decode(ByteBuffer.wrap("not a dump at all".getBytes())) == null, "garbage -> null");
        int thrown = 0;
        for (byte[] data : new byte[][]{real, synth}) {
            for (int n = 0; n < data.length; n++) {
                try { MinidumpDecoder.decode(ByteBuffer.wrap(data, 0, n).slice()); } catch (Throwable t) { thrown++; }
            }
            Random random = new Random(1);
            for (int i = 0; i < 20000; i++) {
                byte[] copy = data.clone();
                for (int k = 0; k < 8; k++) copy[4 + random.nextInt(copy.length - 4)] = (byte)random.nextInt();
                try { MinidumpDecoder.decode(ByteBuffer.wrap(copy)); } catch (Throwable t) { thrown++; }
            }
        }
        check(thrown == 0, "truncated/corrupted dumps never throw (" + thrown + " threw)");
        System.out.println(failures == 0 ? "ALL PASSED" : failures + " FAILED");
        System.exit(failures == 0 ? 0 : 1);
    }
}
