import React from 'react';

export const AvatarEva = ({ isSpeaking = true, className = '', style = {} }) => {
  return (
    <div
      className={`avatar-eva-container ${isSpeaking ? 'avatar-eva-speaking' : ''} ${className}`}
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        userSelect: 'none',
        overflow: 'hidden',
        background: '#FFFFFF',
        borderRadius: '16px',
        ...style,
      }}
    >
      <style>{`
        /* Dynamic Mouth Morphing for Lip-Sync */
        @keyframes talkMouth {
          0%, 100% { transform: scaleY(0.4) translateY(2px); }
          50% { transform: scaleY(1.3) translateY(0px); }
        }

        /* Speaking Glow Pulse Ripple */
        @keyframes evaSpeakingPulse {
          0% {
            box-shadow: 0 0 0 0 rgba(101, 89, 123, 0.45), 0 8px 32px rgba(101, 89, 123, 0.15);
          }
          70% {
            box-shadow: 0 0 0 14px rgba(101, 89, 123, 0), 0 12px 36px rgba(101, 89, 123, 0.25);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(101, 89, 123, 0), 0 8px 32px rgba(101, 89, 123, 0.15);
          }
        }

        .avatar-eva-speaking {
          animation: evaSpeakingPulse 1.8s cubic-bezier(0.4, 0, 0.6, 1) infinite !important;
          border-color: rgba(101, 89, 123, 0.5) !important;
        }

        /* Organic Breathing Motion */
        @keyframes torsoBreathe {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-3px); }
        }

        /* Subtle Head Sway */
        @keyframes headSway {
          0%, 100% { transform: rotate(0deg); }
          50% { transform: rotate(1.5deg); }
        }

        .anim-mouth {
          transform-origin: 275px 225px;
          animation: talkMouth 0.35s ease-in-out infinite alternate;
        }

        .anim-torso {
          transform-origin: bottom center;
          animation: torsoBreathe 4s ease-in-out infinite;
        }

        .anim-head {
          transform-origin: 250px 300px;
          animation: headSway 4.5s ease-in-out infinite;
        }


      `}</style>

      {/* SVG Container with preserveAspectRatio to display the full character without clipping */}
      <svg viewBox="0 25 500 475" preserveAspectRatio="xMidYMid meet" fill="none" xmlns="http://www.w3.org/2000/svg" style={{width: '100%', height: '100%', position: 'absolute', top: 0, left: 0}}>
        
        {/* BACK HAIR LAYER */}
        <g className="anim-head">
          <path d="M 120 350 C 40 320, 40 200, 130 150 C 150 100, 220 40, 300 50 C 400 60, 460 160, 420 280 C 400 340, 380 350, 380 350 L 300 350 L 200 350 Z" fill="#3C3970" />
        </g>

        {/* TORSO LAYER */}
        <g className="anim-torso">
          {/* Shirt */}
          <path d="M 210 350 Q 100 380, -20 450 L -20 520 L 520 520 L 520 450 Q 400 380, 300 350 Q 255 380, 210 350 Z" fill="#F3CAE2" />
          
          {/* Shirt details/strokes */}
          <path d="M 210 350 Q 255 380 300 350" fill="none" stroke="#2B1516" strokeWidth="3" strokeLinecap="round"/>
          <path d="M 210 350 Q 100 380, 0 440" fill="none" stroke="#2B1516" strokeWidth="2.5" opacity="0.6"/>
          <path d="M 300 350 Q 400 380, 500 440" fill="none" stroke="#2B1516" strokeWidth="2.5" opacity="0.6"/>
          
          {/* Neck */}
          <path d="M 210 250 L 210 350 Q 255 380 300 350 L 300 250 Z" fill="#F7ADAB" />
          
          {/* Neck Shadow */}
          <path d="M 230 275 C 270 290, 300 270, 300 240 L 300 350 Q 255 380 210 350 L 210 300 Z" fill="#E58A88" />
        </g>

        {/* HEAD LAYER */}
        <g className="anim-head">
          {/* Face Base Shape */}
          <path d="M 195 210 C 195 250, 210 290, 250 290 C 280 290, 315 270, 315 210 C 315 150, 280 140, 240 140 C 200 140, 195 180, 195 210 Z" fill="#F7ADAB" />
          
          {/* Left Ear */}
          <path d="M 200 190 C 160 190, 160 240, 200 240" fill="#F7ADAB" stroke="#2B1516" strokeWidth="3" />
          <path d="M 185 210 C 195 210, 195 220, 190 225" fill="none" stroke="#2B1516" strokeWidth="2.5" strokeLinecap="round" />
          <circle cx="185" cy="235" r="4.5" fill="#FFFFFF" />

          {/* Blush */}
          <ellipse cx="240" cy="195" rx="11" ry="6" fill="#EE7B78" opacity="0.9" />
          <ellipse cx="290" cy="188" rx="11" ry="6" fill="#EE7B78" opacity="0.9" />

          {/* Eyes (Happy Closed Curves) */}
          <path d="M 230 185 Q 240 175 250 185" fill="none" stroke="#2B1516" strokeWidth="3.5" strokeLinecap="round" />
          <path d="M 275 178 Q 285 168 295 178" fill="none" stroke="#2B1516" strokeWidth="3.5" strokeLinecap="round" />

          {/* Eyebrows */}
          <path d="M 230 168 Q 240 163 250 168" fill="none" stroke="#2B1516" strokeWidth="2.5" strokeLinecap="round" />
          <path d="M 275 160 Q 285 155 295 160" fill="none" stroke="#2B1516" strokeWidth="2.5" strokeLinecap="round" />

          {/* Nose */}
          <path d="M 275 195 C 280 200, 280 205, 275 210" fill="none" stroke="#2B1516" strokeWidth="2.5" strokeLinecap="round" />

          {/* Mouth */}
          <g>
            {isSpeaking ? (
              // Mouth Morph
              <ellipse cx="275" cy="225" rx="7" ry="5" fill="#2B1516" className="anim-mouth" />
            ) : (
              // Static Smirk
              <path d="M 265 225 Q 275 235 285 225" fill="none" stroke="#2B1516" strokeWidth="3" strokeLinecap="round" />
            )}
          </g>

          {/* FRONT HAIR LAYER */}
          {/* Hair swooping from left across the forehead to the right side */}
          <path d="M 230 140 C 260 130, 290 140, 310 180 C 320 210, 310 270, 310 270 C 330 250, 340 180, 330 140 C 320 80, 260 80, 230 140 Z" fill="#3C3970" />
          {/* Inner hair depth shadow */}
          <path d="M 280 140 C 300 160, 310 200, 310 270 C 340 230, 340 150, 280 140 Z" fill="#292652" opacity="0.4"/>
        </g>



      </svg>
    </div>
  );
};

export default AvatarEva;
