package com.winlator.renderer;
import com.winlator.xserver.Drawable;
// Test stand-in: no GL.
public class Texture {
    protected final Drawable owner;
    public Texture(Drawable owner) { this.owner = owner; }
    public void setNeedsUpdate(boolean needsUpdate) {}
    public void destroy() {}
}
