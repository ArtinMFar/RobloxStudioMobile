package com.winlator.xserver;

import com.winlator.renderer.GPUImage;

import java.io.File;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;

// Exercises the patched Drawable with Winlator's real native drawing code (compiled for the host).
public class DrawableTest {
    static int failures = 0;

    static void check(boolean ok, String what) {
        System.out.println((ok ? "PASS " : "FAIL ") + what);
        if (!ok) failures++;
    }

    static ByteBuffer image(int w, int h, int base) {
        ByteBuffer b = ByteBuffer.allocateDirect(w * h * 4).order(ByteOrder.LITTLE_ENDIAN);
        for (int i = 0; i < w * h; i++) b.putInt(i * 4, base + i);
        return b;
    }

    /** A genuinely read-only mapping (PROT_READ), like Winlator's SysV SHM / DRI3 mappings. */
    static ByteBuffer readOnlyMapping(int w, int h, int base) throws Exception {
        File f = File.createTempFile("shm", ".bin");
        f.deleteOnExit();
        try (RandomAccessFile raf = new RandomAccessFile(f, "rw")) {
            raf.setLength((long)w * h * 4);
            ByteBuffer rw = raf.getChannel().map(FileChannel.MapMode.READ_WRITE, 0, (long)w * h * 4).order(ByteOrder.LITTLE_ENDIAN);
            for (int i = 0; i < w * h; i++) rw.putInt(i * 4, base + i);
            return raf.getChannel().map(FileChannel.MapMode.READ_ONLY, 0, (long)w * h * 4).order(ByteOrder.LITTLE_ENDIAN);
        }
    }

    static int px(Drawable d, int x, int y, int stride) {
        return d.getData().getInt((y * stride + x) * 4);
    }

    public static void main(String[] args) throws Exception {
        System.loadLibrary("winlator");
        String mode = args.length > 0 ? args[0] : "all";

        if (mode.equals("old-behaviour")) {
            // What happened on the phone: the window's pixels point at the client's read-only image
            // (not flagged), then a normal ShmPutImage copies into the window.
            Drawable window = new Drawable(1, 64, 48, null);
            window.setData(readOnlyMapping(64, 48, 1000), false);
            System.out.println("writing into read-only mapping without the fix...");
            System.out.flush();
            window.drawImage((short)0, (short)0, (short)0, (short)0, (short)64, (short)48, (byte)24, image(64, 48, 5), (short)64, (short)48);
            System.out.println("no crash?!");
            return;
        }

        // 1. Plain copy is unchanged.
        Drawable d = new Drawable(1, 64, 48, null);
        d.drawImage((short)2, (short)3, (short)10, (short)5, (short)20, (short)10, (byte)24, image(64, 48, 100), (short)64, (short)48);
        check(px(d, 10, 5, 64) == 100 + 3 * 64 + 2, "plain copy: first pixel");
        check(px(d, 29, 14, 64) == 100 + 12 * 64 + 21, "plain copy: last pixel");
        check(px(d, 30, 14, 64) == 0 && px(d, 9, 5, 64) == 0, "plain copy: nothing outside the rectangle");

        // 2. The crash scenario with the fix: read-only borrowed pixels, then a write.
        Drawable w = new Drawable(2, 64, 48, null);
        ByteBuffer ro = readOnlyMapping(64, 48, 7000);
        w.setData(ro, true);
        w.drawImage((short)0, (short)0, (short)4, (short)4, (short)8, (short)8, (byte)24, image(64, 48, 50), (short)64, (short)48);
        check(w.getData() != ro, "read-only borrowed buffer replaced by a writable one");
        check(px(w, 4, 4, 64) == 50, "new image drawn");
        check(px(w, 0, 0, 64) == 7000 && px(w, 63, 47, 64) == 7000 + 47 * 64 + 63, "previous pixels kept (copied out of the read-only buffer)");
        check(ro.getInt(4 * 4 * 64 + 16) == 7000 + 4 * 64 + 4, "client's read-only buffer untouched");
        Drawable ref = new Drawable(9, 8, 8, null);
        ref.fillRect(0, 0, 8, 8, 0x12345678);
        int filled = px(ref, 1, 1, 8);
        ref.fillRect(0, 0, 8, 8, 0x55);
        int filled55 = px(ref, 1, 1, 8);
        w.fillRect(0, 0, 2, 2, 0x12345678);
        check(px(w, 1, 1, 64) == filled, "fillRect works after the switch");

        // 3. Other writers on a read-only drawable (fillRect / copyArea) also switch first.
        Drawable f = new Drawable(3, 32, 32, null);
        f.setData(readOnlyMapping(32, 32, 1), true);
        f.fillRect(0, 0, 32, 32, 0x55);
        check(px(f, 31, 31, 32) == filled55, "fillRect on read-only drawable");
        Drawable c = new Drawable(4, 32, 32, null);
        c.setData(readOnlyMapping(32, 32, 1), true);
        c.copyArea((short)0, (short)0, (short)0, (short)0, (short)32, (short)32, f);
        check(px(c, 5, 5, 32) == filled55 && c.getData().capacity() == 32 * 32 * 4, "copyArea into read-only drawable");

        // 4. Bounds: source buffer smaller than the request claims -> clipped, no overflow.
        Drawable b = new Drawable(5, 64, 48, null);
        b.drawImage((short)0, (short)0, (short)0, (short)0, (short)64, (short)48, (byte)24, image(64, 4, 9), (short)64, (short)48);
        check(px(b, 63, 3, 64) == 9 + 3 * 64 + 63 && px(b, 0, 4, 64) == 0, "short source buffer: only the 4 existing rows copied");
        b.drawImage((short)60, (short)0, (short)0, (short)0, (short)30, (short)2, (byte)24, image(64, 2, 3), (short)64, (short)2);
        check(px(b, 3, 0, 64) == 3 + 63 && px(b, 4, 0, 64) == 9 + 4, "source wider than its stride: clipped to 4 columns");
        b.drawImage((short)0, (short)0, (short)60, (short)45, (short)64, (short)48, (byte)24, image(64, 48, 1), (short)64, (short)48);
        check(px(b, 63, 47, 64) == 1 + 2 * 64 + 3, "destination overflow clipped");

        // 5. Negative destination moves the source with it (was: clamped without moving source).
        Drawable n = new Drawable(6, 16, 16, null);
        n.drawImage((short)0, (short)0, (short)-3, (short)-2, (short)8, (short)8, (byte)24, image(16, 16, 200), (short)16, (short)16);
        check(px(n, 0, 0, 16) == 200 + 2 * 16 + 3, "negative destination clipped correctly");

        // 6. GPU buffer stride only used while pixels are in the GPU buffer.
        Drawable g = new Drawable(7, 64, 48, null);
        GPUImage gpu = new GPUImage(g, (short)80);
        g.setTexture(gpu);
        g.drawImage((short)0, (short)0, (short)0, (short)1, (short)64, (short)1, (byte)24, image(64, 48, 300), (short)64, (short)48);
        check(gpu.getVirtualData().getInt((1 * 80 + 63) * 4) == 363, "GPU buffer written with its 80-pixel stride");
        ByteBuffer ro2 = readOnlyMapping(64, 48, 4000);
        g.setData(ro2, true);
        g.drawImage((short)0, (short)0, (short)0, (short)0, (short)1, (short)1, (byte)24, image(1, 1, 9), (short)1, (short)1);
        check(g.getData() == gpu.getVirtualData(), "read-only pixels moved back into the GPU buffer");
        check(gpu.getVirtualData().getInt((47 * 80 + 63) * 4) == 4000 + 47 * 64 + 63, "copied with the right strides (64 -> 80)");
        check(gpu.getVirtualData().getInt(0) == 9, "new pixel drawn into GPU buffer");

        System.out.println(failures == 0 ? "ALL PASSED" : failures + " FAILED");
        System.exit(failures == 0 ? 0 : 1);
    }
}
