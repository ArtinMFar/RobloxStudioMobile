package com.winlator.renderer;
import com.winlator.xserver.Drawable;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
// Test stand-in for a CPU-mapped AHardwareBuffer with a padded stride.
public class GPUImage extends Texture {
    private final ByteBuffer virtualData;
    private final short stride;
    public GPUImage(Drawable owner, short stride) {
        super(owner);
        this.stride = stride;
        this.virtualData = ByteBuffer.allocateDirect(stride * owner.height * 4).order(ByteOrder.LITTLE_ENDIAN);
    }
    public short getStride() { return stride; }
    public ByteBuffer getVirtualData() { return virtualData; }
}
