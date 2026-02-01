import { Check, ShoppingCart, Trash2, Plus, Minus, AlertCircle, Info, ArrowRight, ArrowLeft } from 'lucide-react';
import { Button } from '@/app/components/ui/button';
import { designTokens } from '@/app/design-tokens';

export function StyleGuide() {
  const handleBack = () => {
    window.location.reload(); // Simple way to go back to main app
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-[#f5d7b1] px-8 py-6 border-b border-[#e5c7a1] sticky top-0 z-10">
        <div className="flex items-center gap-4 mb-2">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-[#6b5f4a] hover:text-[#4a3f2a] hover:bg-[#f5e6d3] rounded transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to App
          </button>
        </div>
        <h1 className="text-3xl text-[#4a3f2a]" style={{ fontFamily: 'Georgia, serif' }}>
          Conscious Cart Coach Design System
        </h1>
        <p className="text-[#6b5f4a] mt-2">
          A comprehensive guide to colors, typography, components, and design patterns
        </p>
      </header>

      <div className="max-w-7xl mx-auto px-8 py-12 space-y-16">
        
        {/* Introduction */}
        <section>
          <h2 className="text-2xl mb-4 text-[#4a3f2a]">Design Philosophy</h2>
          <div className="bg-[#fef4e6] border border-[#e5d5b8] rounded-lg p-6">
            <p className="text-[#6b5f4a] mb-4">
              The Conscious Cart Coach design system emphasizes sustainability, warmth, and clarity.
              Our color palette draws from natural earth tones, creating a trustworthy and approachable
              experience that aligns with ethical shopping values.
            </p>
            <ul className="space-y-2">
              <li className="flex items-start gap-2 text-[#6b5f4a]">
                <Check className="w-5 h-5 text-[#7a6f4a] flex-shrink-0 mt-0.5" />
                <span><strong>Warm & Natural:</strong> Earth tones convey sustainability and organic choices</span>
              </li>
              <li className="flex items-start gap-2 text-[#6b5f4a]">
                <Check className="w-5 h-5 text-[#7a6f4a] flex-shrink-0 mt-0.5" />
                <span><strong>Clear Hierarchy:</strong> Visual distinction guides users through complex decisions</span>
              </li>
              <li className="flex items-start gap-2 text-[#6b5f4a]">
                <Check className="w-5 h-5 text-[#7a6f4a] flex-shrink-0 mt-0.5" />
                <span><strong>Accessible:</strong> High contrast and semantic colors ensure readability</span>
              </li>
            </ul>
          </div>
        </section>

        {/* Color Palette */}
        <section>
          <h2 className="text-2xl mb-6 text-[#4a3f2a]">Color Palette</h2>
          
          {/* Brand Colors */}
          <div className="mb-8">
            <h3 className="text-xl mb-4 text-[#4a3f2a]">Brand Colors</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <ColorSwatch 
                name="Primary" 
                color="#6b5f3a" 
                textColor="white"
                usage="Primary actions, main CTAs"
              />
              <ColorSwatch 
                name="Primary Hover" 
                color="#5b4f2a" 
                textColor="white"
                usage="Hover states for primary"
              />
              <ColorSwatch 
                name="Primary Light" 
                color="#8b7a5a" 
                textColor="white"
                usage="Borders, subtle accents"
              />
              <ColorSwatch
                name="Accent"
                color="#DD9057"
                textColor="white"
                usage="Secondary actions"
              />
              <ColorSwatch
                name="Accent Hover"
                color="#C87040"
                textColor="white"
                usage="Hover states for accent"
              />
            </div>
          </div>

          {/* Background Colors */}
          <div className="mb-8">
            <h3 className="text-xl mb-4 text-[#4a3f2a]">Background Colors</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <ColorSwatch 
                name="Page" 
                color="#f5e6d3" 
                textColor="#4a3f2a"
                usage="Main page background"
              />
              <ColorSwatch 
                name="Header" 
                color="#f5d7b1" 
                textColor="#4a3f2a"
                usage="Header background"
              />
              <ColorSwatch 
                name="Card" 
                color="#ffffff" 
                textColor="#4a3f2a"
                usage="Cards, panels"
              />
              <ColorSwatch 
                name="Input" 
                color="#fef4e6" 
                textColor="#4a3f2a"
                usage="Input fields"
              />
              <ColorSwatch 
                name="Light Accent" 
                color="#f5e6d3" 
                textColor="#4a3f2a"
                usage="Light backgrounds"
              />
            </div>
          </div>

          {/* Text Colors */}
          <div className="mb-8">
            <h3 className="text-xl mb-4 text-[#4a3f2a]">Text Colors</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <ColorSwatch 
                name="Primary Text" 
                color="#4a3f2a" 
                textColor="white"
                usage="Headings, primary content"
              />
              <ColorSwatch 
                name="Secondary Text" 
                color="#6b5f4a" 
                textColor="white"
                usage="Body text, descriptions"
              />
              <ColorSwatch 
                name="Tertiary Text" 
                color="#8b7a5a" 
                textColor="white"
                usage="Labels, captions"
              />
              <ColorSwatch 
                name="White Text" 
                color="#ffffff" 
                textColor="#4a3f2a"
                usage="Text on dark backgrounds"
              />
            </div>
          </div>

          {/* Ethical Tags */}
          <div className="mb-8">
            <h3 className="text-xl mb-4 text-[#4a3f2a]">Ethical Tags</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <ColorSwatch 
                name="Organic" 
                color="#e8f5e9" 
                textColor="#2e7d32"
                usage="Organic products"
              />
              <ColorSwatch 
                name="Local" 
                color="#e3f2fd" 
                textColor="#1565c0"
                usage="Locally sourced"
              />
              <ColorSwatch 
                name="Best Value" 
                color="#fff8e1" 
                textColor="#f57c00"
                usage="Best price/value"
              />
              <ColorSwatch 
                name="Seasonal" 
                color="#f3e5f5" 
                textColor="#6a1b9a"
                usage="Seasonal items"
              />
              <ColorSwatch 
                name="Low Packaging" 
                color="#fce4ec" 
                textColor="#c2185b"
                usage="Eco-friendly packaging"
              />
            </div>
          </div>
        </section>

        {/* Typography */}
        <section>
          <h2 className="text-2xl mb-6 text-[#4a3f2a]">Typography</h2>
          
          <div className="space-y-8">
            {/* Font Families */}
            <div>
              <h3 className="text-xl mb-4 text-[#4a3f2a]">Font Families</h3>
              <div className="space-y-4 bg-[#fef4e6] border border-[#e5d5b8] rounded-lg p-6">
                <div>
                  <p className="text-sm text-[#8b7a5a] mb-1">Primary (System UI)</p>
                  <p className="text-2xl text-[#4a3f2a]" style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}>
                    The quick brown fox jumps over the lazy dog
                  </p>
                </div>
                <div>
                  <p className="text-sm text-[#8b7a5a] mb-1">Heading (Georgia Serif)</p>
                  <p className="text-2xl text-[#4a3f2a]" style={{ fontFamily: 'Georgia, serif' }}>
                    The quick brown fox jumps over the lazy dog
                  </p>
                </div>
              </div>
            </div>

            {/* Font Sizes */}
            <div>
              <h3 className="text-xl mb-4 text-[#4a3f2a]">Font Sizes</h3>
              <div className="space-y-3 bg-[#fef4e6] border border-[#e5d5b8] rounded-lg p-6">
                <div className="flex items-baseline gap-4">
                  <span className="text-xs text-[#4a3f2a] w-16">xs (12px)</span>
                  <span className="text-xs text-[#4a3f2a]">Small labels and captions</span>
                </div>
                <div className="flex items-baseline gap-4">
                  <span className="text-sm text-[#4a3f2a] w-16">sm (14px)</span>
                  <span className="text-sm text-[#4a3f2a]">Secondary text and metadata</span>
                </div>
                <div className="flex items-baseline gap-4">
                  <span className="text-base text-[#4a3f2a] w-16">base (16px)</span>
                  <span className="text-base text-[#4a3f2a]">Body text and primary content</span>
                </div>
                <div className="flex items-baseline gap-4">
                  <span className="text-lg text-[#4a3f2a] w-16">lg (18px)</span>
                  <span className="text-lg text-[#4a3f2a]">Subheadings and emphasis</span>
                </div>
                <div className="flex items-baseline gap-4">
                  <span className="text-xl text-[#4a3f2a] w-16">xl (20px)</span>
                  <span className="text-xl text-[#4a3f2a]">Section headings</span>
                </div>
                <div className="flex items-baseline gap-4">
                  <span className="text-2xl text-[#4a3f2a] w-16">2xl (24px)</span>
                  <span className="text-2xl text-[#4a3f2a]">Page headings</span>
                </div>
              </div>
            </div>

            {/* Font Weights */}
            <div>
              <h3 className="text-xl mb-4 text-[#4a3f2a]">Font Weights</h3>
              <div className="space-y-3 bg-[#fef4e6] border border-[#e5d5b8] rounded-lg p-6">
                <p className="text-[#4a3f2a]" style={{ fontWeight: 400 }}>Normal (400) - Body text</p>
                <p className="text-[#4a3f2a]" style={{ fontWeight: 500 }}>Medium (500) - Headings and labels</p>
                <p className="text-[#4a3f2a]" style={{ fontWeight: 600 }}>Semibold (600) - Strong emphasis</p>
                <p className="text-[#4a3f2a]" style={{ fontWeight: 700 }}>Bold (700) - Maximum emphasis</p>
              </div>
            </div>
          </div>
        </section>

        {/* Spacing */}
        <section>
          <h2 className="text-2xl mb-6 text-[#4a3f2a]">Spacing Scale</h2>
          <div className="bg-[#fef4e6] border border-[#e5d5b8] rounded-lg p-6">
            <div className="space-y-4">
              {[
                { name: '1', value: '4px', size: '0.25rem' },
                { name: '2', value: '8px', size: '0.5rem' },
                { name: '3', value: '12px', size: '0.75rem' },
                { name: '4', value: '16px', size: '1rem' },
                { name: '6', value: '24px', size: '1.5rem' },
                { name: '8', value: '32px', size: '2rem' },
                { name: '12', value: '48px', size: '3rem' },
              ].map((space) => (
                <div key={space.name} className="flex items-center gap-4">
                  <span className="text-sm text-[#8b7a5a] w-12">{space.name}</span>
                  <span className="text-sm text-[#6b5f4a] w-20">{space.value}</span>
                  <div 
                    className="bg-[#6b5f3a] h-6" 
                    style={{ width: space.size }}
                  />
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Buttons */}
        <section>
          <h2 className="text-2xl mb-6 text-[#4a3f2a]">Buttons</h2>
          
          <div className="space-y-8">
            {/* Primary Buttons */}
            <div>
              <h3 className="text-lg mb-4 text-[#4a3f2a]">Primary Buttons</h3>
              <div className="flex flex-wrap gap-4 bg-[#fef4e6] border border-[#e5d5b8] rounded-lg p-6">
                <Button className="bg-[#6b5f3a] hover:bg-[#5b4f2a] text-white">
                  Primary Button
                </Button>
                <Button className="bg-[#6b5f3a] hover:bg-[#5b4f2a] text-white">
                  <ShoppingCart className="w-4 h-4 mr-2" />
                  With Icon
                </Button>
                <Button className="bg-[#6b5f3a] hover:bg-[#5b4f2a] text-white">
                  Continue
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
                <Button disabled className="bg-[#c5baa8] opacity-50 cursor-not-allowed text-white">
                  Disabled
                </Button>
              </div>
            </div>

            {/* Secondary Buttons */}
            <div>
              <h3 className="text-lg mb-4 text-[#4a3f2a]">Secondary Buttons</h3>
              <div className="flex flex-wrap gap-4 bg-[#fef4e6] border border-[#e5d5b8] rounded-lg p-6">
                <Button className="bg-[#DD9057] hover:bg-[#C87040] text-white">
                  Secondary Button
                </Button>
                <Button className="bg-[#DD9057] hover:bg-[#C87040] text-white">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Item
                </Button>
                <Button disabled className="bg-[#EDD4C0] opacity-70 cursor-not-allowed text-white">
                  Disabled
                </Button>
              </div>
            </div>

            {/* Outline Buttons */}
            <div>
              <h3 className="text-lg mb-4 text-[#4a3f2a]">Outline Buttons</h3>
              <div className="flex flex-wrap gap-4 bg-[#fef4e6] border border-[#e5d5b8] rounded-lg p-6">
                <Button variant="outline" className="border-[#8b7a5a] text-[#6b5f4a] hover:bg-[#f5e6d3]">
                  Outline Button
                </Button>
                <Button variant="outline" className="border-[#8b7a5a] text-[#6b5f4a] hover:bg-[#f5e6d3]">
                  <Info className="w-4 h-4 mr-2" />
                  With Icon
                </Button>
                <Button variant="outline" disabled className="border-[#8b7a5a] text-[#6b5f4a] opacity-50 cursor-not-allowed">
                  Disabled
                </Button>
              </div>
            </div>

            {/* Icon Buttons */}
            <div>
              <h3 className="text-lg mb-4 text-[#4a3f2a]">Icon Buttons</h3>
              <div className="flex flex-wrap gap-4 bg-[#fef4e6] border border-[#e5d5b8] rounded-lg p-6">
                <Button variant="outline" size="sm" className="border-[#8b7a5a] text-[#6b5f4a]">
                  <Plus className="w-4 h-4" />
                </Button>
                <Button variant="outline" size="sm" className="border-[#8b7a5a] text-[#6b5f4a]">
                  <Minus className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm" className="text-[#c9665a]">
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Tags/Badges */}
        <section>
          <h2 className="text-2xl mb-6 text-[#4a3f2a]">Tags & Badges</h2>
          <div className="bg-[#fef4e6] border border-[#e5d5b8] rounded-lg p-6">
            <div className="flex flex-wrap gap-3">
              <span className="px-3 py-1 bg-[#e8f5e9] text-[#2e7d32] rounded-full text-xs font-medium">
                Organic
              </span>
              <span className="px-3 py-1 bg-[#e3f2fd] text-[#1565c0] rounded-full text-xs font-medium">
                Local
              </span>
              <span className="px-3 py-1 bg-[#fff8e1] text-[#f57c00] rounded-full text-xs font-medium">
                Best Value
              </span>
              <span className="px-3 py-1 bg-[#f3e5f5] text-[#6a1b9a] rounded-full text-xs font-medium">
                Seasonal
              </span>
              <span className="px-3 py-1 bg-[#fce4ec] text-[#c2185b] rounded-full text-xs font-medium">
                Low Packaging
              </span>
            </div>
          </div>
        </section>

        {/* Icons */}
        <section>
          <h2 className="text-2xl mb-6 text-[#4a3f2a]">Icons</h2>
          <div className="bg-[#fef4e6] border border-[#e5d5b8] rounded-lg p-6">
            <p className="text-sm text-[#6b5f4a] mb-4">Using Lucide React icons throughout the application</p>
            <div className="flex flex-wrap gap-6">
              <div className="flex flex-col items-center gap-2">
                <ShoppingCart className="w-6 h-6 text-[#6b5f3a]" />
                <span className="text-xs text-[#8b7a5a]">Cart</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <Check className="w-6 h-6 text-[#7a6f4a]" />
                <span className="text-xs text-[#8b7a5a]">Check</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <Plus className="w-6 h-6 text-[#6b5f3a]" />
                <span className="text-xs text-[#8b7a5a]">Plus</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <Minus className="w-6 h-6 text-[#6b5f3a]" />
                <span className="text-xs text-[#8b7a5a]">Minus</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <Trash2 className="w-6 h-6 text-[#c9665a]" />
                <span className="text-xs text-[#8b7a5a]">Delete</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <ArrowRight className="w-6 h-6 text-[#6b5f3a]" />
                <span className="text-xs text-[#8b7a5a]">Arrow</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <Info className="w-6 h-6 text-[#6b5f4a]" />
                <span className="text-xs text-[#8b7a5a]">Info</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <AlertCircle className="w-6 h-6 text-[#d9b899]" />
                <span className="text-xs text-[#8b7a5a]">Alert</span>
              </div>
            </div>
          </div>
        </section>

        {/* Component Examples */}
        <section>
          <h2 className="text-2xl mb-6 text-[#4a3f2a]">Component Examples</h2>
          
          {/* Input Field */}
          <div className="mb-8">
            <h3 className="text-lg mb-4 text-[#4a3f2a]">Input Field</h3>
            <div className="bg-[#fef4e6] border border-[#e5d5b8] rounded p-4 max-w-md">
              <label className="text-xs text-[#6b5f4a] block mb-2">
                Example input label
              </label>
              <textarea
                placeholder="Enter your text here..."
                className="w-full bg-transparent border-none outline-none text-[#4a3f2a] resize-none min-h-[100px]"
              />
            </div>
          </div>

          {/* Product Card Preview */}
          <div className="mb-8">
            <h3 className="text-lg mb-4 text-[#4a3f2a]">Product Card</h3>
            <div className="bg-white border border-[#e5d5b8] rounded-lg p-4 max-w-md">
              <div className="flex gap-4">
                <div className="w-20 h-20 bg-[#f5e6d3] rounded flex items-center justify-center">
                  <ShoppingCart className="w-8 h-8 text-[#8b7a5a]" />
                </div>
                <div className="flex-1">
                  <h4 className="text-[#4a3f2a] font-medium mb-1">Product Name</h4>
                  <p className="text-sm text-[#6b5f4a] mb-2">Brief description</p>
                  <div className="flex gap-2">
                    <span className="px-2 py-0.5 bg-[#e8f5e9] text-[#2e7d32] rounded-full text-xs">
                      Organic
                    </span>
                    <span className="px-2 py-0.5 bg-[#e3f2fd] text-[#1565c0] rounded-full text-xs">
                      Local
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Design Tokens Reference */}
        <section>
          <h2 className="text-2xl mb-6 text-[#4a3f2a]">Using Design Tokens</h2>
          <div className="bg-[#fef4e6] border border-[#e5d5b8] rounded-lg p-6">
            <p className="text-[#6b5f4a] mb-4">
              Import and use design tokens in your components for consistency:
            </p>
            <pre className="bg-white border border-[#e5d5b8] rounded p-4 text-sm overflow-x-auto">
              <code className="text-[#4a3f2a]">{`import { designTokens } from '@/app/design-tokens';

// Use in inline styles
<div style={{ 
  color: designTokens.colors.text.primary,
  backgroundColor: designTokens.colors.background.page 
}}>
  Content
</div>

// Reference in Tailwind classes
<div className="text-[#4a3f2a] bg-[#f5e6d3]">
  Content
</div>`}</code>
            </pre>
          </div>
        </section>

      </div>
    </div>
  );
}

// Color Swatch Component
interface ColorSwatchProps {
  name: string;
  color: string;
  textColor: string;
  usage: string;
}

function ColorSwatch({ name, color, textColor, usage }: ColorSwatchProps) {
  return (
    <div className="border border-[#e5d5b8] rounded-lg overflow-hidden">
      <div 
        className="h-24 flex items-center justify-center"
        style={{ backgroundColor: color, color: textColor }}
      >
        <span className="font-medium text-sm">{name}</span>
      </div>
      <div className="p-3 bg-white">
        <p className="text-xs font-mono text-[#6b5f4a] mb-1">{color}</p>
        <p className="text-xs text-[#8b7a5a]">{usage}</p>
      </div>
    </div>
  );
}