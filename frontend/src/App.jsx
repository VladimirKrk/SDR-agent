import React, { useState, useEffect } from 'react';
import ReactFlow, { Background, Controls, useNodesState, useEdgesState } from 'reactflow';
import 'reactflow/dist/style.css';
import { Play, Terminal, Mail, User, CheckCircle } from 'lucide-react';

// Compact Node Layout
const initialNodes = [
  { id: '1', position: { x: 50, y: 50 }, data: { label: '🔎 Discovery' }, style: { width: 150, background: '#1e1e1e', color: '#fff', border: '1px solid #555' } },
  { id: '2', position: { x: 250, y: 50 }, data: { label: '🕸️ Scout' }, style: { width: 150, background: '#1e1e1e', color: '#fff', border: '1px solid #555' } },
  { id: '3', position: { x: 450, y: 50 }, data: { label: '🧠 Gatekeeper' }, style: { width: 150, background: '#1e1e1e', color: '#fff', border: '1px solid #555' } },
  { id: '4', position: { x: 650, y: 50 }, data: { label: '🕵️‍♂️ Hunter' }, style: { width: 150, background: '#1e1e1e', color: '#fff', border: '1px solid #555' } },
  { id: '5', position: { x: 850, y: 50 }, data: { label: '✍️ Writer' }, style: { width: 150, background: '#1e1e1e', color: '#fff', border: '1px solid #555' } },
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: false },
  { id: 'e2-3', source: '2', target: '3', animated: false },
  { id: 'e3-4', source: '3', target: '4', animated: false },
  { id: 'e4-5', source: '4', target: '5', animated: false },
];

export default function App() {
  const [nodes, setNodes] = useNodesState(initialNodes);
  const [edges, setEdges] = useEdgesState(initialEdges);
  
  const [niche, setNiche] = useState('Marketing Agencies in Austin');
  const [count, setCount] = useState(1);
  const [logs, setLogs] = useState([]);
  const [results, setResults] = useState([]); 
  const [selectedLead, setSelectedLead] = useState(null); 
  const [isRunning, setIsRunning] = useState(false);

  // --- FETCH HISTORY ON LOAD ---
  useEffect(() => {
    fetch('http://localhost:8000/api/history')
      .then(res => res.json())
      .then(data => {
        if (data && data.length > 0) {
          setResults(data);
          // Optional: Auto-select the most recent one
          setSelectedLead(data[data.length - 1]);
        }
      })
      .catch(err => console.error("Could not load history", err));
  }, []);

  // Helper to reset graph colors
  // If keepDiscovery is true, Node 1 stays green. Otherwise, all reset to gray.
  const resetGraph = (keepDiscovery = false) => {
    setNodes((nds) => nds.map((n) => {
      // Keep Discovery green if we are starting a new lead in the loop
      if (keepDiscovery && n.id === '1') {
          return n; 
      }
      return { 
          ...n, 
          style: { ...n.style, background: '#1e1e1e', color: '#fff', borderColor: '#555', boxShadow: 'none' } 
      };
    }));
    
    setEdges((eds) => eds.map((e) => ({ ...e, animated: false, style: { stroke: '#555' } })));
  };

  const startMission = () => {
    setIsRunning(true);
    setLogs((prev) => [...prev, "🚀 Initializing connection..."]);
    
    // FULL RESET when starting a brand new mission
    resetGraph(false); 

    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = () => {
      ws.send(JSON.stringify({ niche, count }));
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === 'log') {
        setLogs((prev) => [...prev, `> ${msg.message}`]);
        
        // PARTIAL RESET when moving to the next lead (Keeps Discovery green)
        if (msg.message.startsWith("Processing:")) {
            resetGraph(true); 
        }
      }

      if (msg.type === 'node_active') {
        setNodes((nds) =>
          nds.map((n) => {
            if (n.id === msg.node) {
              return { ...n, style: { ...n.style, borderColor: '#00FF94', boxShadow: '0 0 15px #00FF94' } };
            }
            return n;
          })
        );
        // Animate edge
        setEdges((eds) => eds.map(e => e.target === msg.node ? { ...e, animated: true, style: { stroke: '#00FF94' } } : e));
      }

      if (msg.type === 'node_done') {
        setNodes((nds) =>
          nds.map((n) => {
            if (n.id === msg.node) {
              return { ...n, style: { ...n.style, background: '#00FF94', color: '#000', borderColor: '#00FF94' } };
            }
            return n;
          })
        );
      }

      if (msg.type === 'result') {
        setResults((prev) => {
            const newResults = [...prev, msg.data];
            setSelectedLead(msg.data); 
            return newResults;
        });
      }

      if (msg.type === 'error' || msg.message === "🏁 Mission Complete.") {
          setIsRunning(false);
      }
    };
  };

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#000', color: 'white', display: 'flex', flexDirection: 'column', fontFamily: 'Inter, sans-serif' }}>
      
      {/* HEADER */}
      <div style={{ height: '70px', padding: '0 20px', borderBottom: '1px solid #333', display: 'flex', gap: '20px', alignItems: 'center', background: '#050505' }}>
        <h2 style={{ color: '#00FF94', margin: 0, display:'flex', alignItems:'center', gap:'10px', fontSize: '20px' }}>📡 Krykos SDR</h2>
        
        <input 
          value={niche} 
          onChange={(e) => setNiche(e.target.value)} 
          placeholder="Target Niche"
          style={{ background: '#111', border: '1px solid #444', color: 'white', padding: '8px', borderRadius: '5px', width: '300px' }}
        />
        
        <div style={{display:'flex', alignItems:'center', gap:'5px', background:'#111', padding:'5px 10px', borderRadius:'5px', border:'1px solid #444'}}>
            <span style={{fontSize:'12px', color:'#888'}}>Limit:</span>
            <input 
            type="number" min="1" max="10" value={count} 
            onChange={(e) => setCount(e.target.value)} 
            style={{ background: 'transparent', border: 'none', color: 'white', width: '40px', textAlign:'center', fontWeight:'bold' }}
            />
        </div>

        <button 
          onClick={startMission} 
          disabled={isRunning}
          style={{ background: '#00FF94', border: 'none', padding: '8px 20px', borderRadius: '5px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px', marginLeft: 'auto' }}
        >
          <Play size={16} /> {isRunning ? 'Running...' : 'Launch Agent'}
        </button>
      </div>

      {/* GRAPH AREA (Compact) */}
      <div style={{ height: '200px', borderBottom: '1px solid #333', background: '#080808' }}>
        <ReactFlow nodes={nodes} edges={edges} fitView>
          <Background color="#111" gap={20} />
        </ReactFlow>
      </div>

      {/* WORKSPACE (Big Area) */}
      <div style={{ flex: 1, display: 'flex', background: '#000', overflow: 'hidden' }}>
        
        {/* LOGS */}
        <div style={{ width: '250px', borderRight: '1px solid #333', padding: '15px', fontFamily: 'monospace', fontSize: '11px', overflowY: 'auto', background:'#050505', color: '#888' }}>
          <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: 0, color:'#ccc', fontSize: '12px' }}><Terminal size={14}/> TERMINAL</h4>
          {logs.map((l, i) => <div key={i} style={{ marginBottom: '4px', whiteSpace: 'pre-wrap' }}>{l}</div>)}
        </div>

        {/* INBOX LIST */}
        <div style={{ width: '300px', borderRight: '1px solid #333', overflowY: 'auto', background:'#080808' }}>
            <h4 style={{ padding: '15px', margin: 0, borderBottom:'1px solid #333', display:'flex', alignItems:'center', gap:'8px', fontSize: '14px' }}><Mail size={16}/> Drafts ({results.length})</h4>
            {results.map((lead, i) => (
                <div 
                    key={i}
                    onClick={() => setSelectedLead(lead)}
                    style={{
                        padding: '15px', 
                        borderBottom: '1px solid #222', 
                        cursor: 'pointer', 
                        background: selectedLead === lead ? '#1A1A1A' : 'transparent',
                        borderLeft: selectedLead === lead ? '3px solid #00FF94' : '3px solid transparent',
                        transition: 'background 0.2s'
                    }}
                >
                    <div style={{fontWeight:'bold', fontSize:'13px', color: '#fff'}}>{lead.company || "Unknown Company"}</div>
                    <div style={{fontSize:'12px', color:'#666', marginTop: '4px'}}>{lead.person || 'Unknown Person'}</div>
                </div>
            ))}
        </div>

        {/* EMAIL PREVIEW (Maximized) */}
        <div style={{ flex: 1, padding: '40px', background:'#111', overflowY:'auto' }}>
          {selectedLead ? (
            <div style={{ maxWidth: '800px', margin:'0 auto', background: '#fff', color: '#000', borderRadius: '8px', boxShadow: '0 4px 30px rgba(0,0,0,0.5)', overflow: 'hidden' }}>
                
                {/* Header */}
                <div style={{ padding: '30px', borderBottom: '1px solid #eee', background: '#f9f9f9' }}>
                    <h1 style={{fontSize:'20px', fontWeight:'bold', margin: '0 0 15px 0', color: '#222'}}>{selectedLead.email_subject}</h1>
                    <div style={{display:'flex', alignItems:'center', gap:'12px'}}>
                        <div style={{width:'36px', height:'36px', borderRadius:'50%', background:'#444', color: '#fff', display:'flex', alignItems:'center', justifyContent:'center', fontWeight: 'bold'}}>
                            {selectedLead.person && selectedLead.person !== 'Unknown' ? selectedLead.person[0] : 'U'}
                        </div>
                        <div>
                            <div style={{fontSize:'13px', fontWeight:'bold'}}>To: {selectedLead.person}</div>
                            <div style={{fontSize:'12px', color:'#666'}}>Analysis by Krykos Scout</div>
                        </div>
                    </div>
                </div>
                
                {/* Body */}
                <div style={{ padding: '40px', fontSize: '15px', lineHeight: '1.6', color: '#333', fontFamily: 'Arial, sans-serif' }}>
                    {selectedLead.email_body ? selectedLead.email_body.split('\n').map((line, i) => (
                        <div key={i} style={{ minHeight: '1em' }}>{line}</div>
                    )) : "No draft available."}
                </div>

                {/* Footer Actions */}
                <div style={{ padding: '20px 30px', background: '#f5f5f5', borderTop: '1px solid #eee', display: 'flex', gap: '15px' }}>
                    {selectedLead.website && (
                        <a href={selectedLead.website} target="_blank" rel="noreferrer" style={{fontSize:'13px', color:'#333', textDecoration:'none', fontWeight: 'bold'}}>
                            Visit Website ↗
                        </a>
                    )}
                    {selectedLead.x_url && (
                        <a href={selectedLead.x_url} target="_blank" rel="noreferrer" style={{fontSize:'13px', color:'#1DA1F2', textDecoration:'none', fontWeight: 'bold'}}>
                            Open X Profile ↗
                        </a>
                    )}
                    {selectedLead.linkedin_url && (
                        <a href={selectedLead.linkedin_url} target="_blank" rel="noreferrer" style={{fontSize:'13px', color:'#0077b5', textDecoration:'none', fontWeight: 'bold'}}>
                            Open LinkedIn ↗
                        </a>
                    )}
                </div>
            </div>
          ) : (
            <div style={{display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', height:'100%', color:'#444'}}>
                <CheckCircle size={48} style={{marginBottom: '20px', opacity: 0.5}} />
                <div>Select a lead to review strategy & draft</div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}