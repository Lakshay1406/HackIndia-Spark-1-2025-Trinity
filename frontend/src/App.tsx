import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Trash2, Plus, FileUp, File, Menu, X, Upload } from 'lucide-react';
import * as pdfjsLib from 'pdfjs-dist';
// Message type definition
interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

// Invoice type definition
interface Invoice {
  id: string;
  name: string;
  uploadDate: Date;
  messages: Message[];
  previewUrl?: string;
}

function App() {
  // State for invoices and current invoice
  const [invoices, setInvoices] = useState<Invoice[]>(() => {
    const saved = localStorage.getItem('invoices');
    return saved ? JSON.parse(saved) : [];
  });
  
  const [currentInvoiceId, setCurrentInvoiceId] = useState<string>(() => {
    return invoices[0]?.id || '';
  });
  
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Get current invoice
  const currentInvoice = invoices.find(inv => inv.id === currentInvoiceId);

  // Save invoices to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('invoices', JSON.stringify(invoices));
  }, [invoices]);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentInvoice?.messages]);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  // Handle file upload
  const handleFileUpload = async(e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setIsUploading(true);
    
    // Create a preview URL for the file
    const isPdf = file.type === 'application/pdf';
    const previewUrl = URL.createObjectURL(file);
    
    // Simulate file upload and processing
    setTimeout(async () => {
      const newInvoice: Invoice = {
        id: Date.now().toString(),
        name: file.name,
        uploadDate: new Date(),
        messages: [],
        previewUrl
      };
      const formData = new FormData();
  formData.append('file', file);

    try {
      // Send the file to the backend using a POST request
      const response = await fetch('http://127.0.0.1:8000/file', {
        method: 'POST',
        body: formData,
      });
    

      // Handle the response from the backend
      if (response.ok) {
        const responseData = async()=>{await response.json()};
        console.log('File uploaded successfully:', responseData);
        
        // You can now handle the uploaded file's response (e.g., preview URL or file ID)
        // For example, if the backend returns a preview URL, set it in the state:
        // const previewUrl = responseData.previewUrl;  // Example field from response
        setInvoices(prevInvoices => [
          { id: Date.now().toString(), name: file.name, previewUrl, uploadDate: new Date(), messages: [] },
          ...prevInvoices
        ]);
      } else {
        console.error('File upload failed:', response.statusText);
      }
    } catch (error) {
      console.error('Error during file upload:', error);
    } finally {
      // Set uploading state to false after the request is completed
      setIsUploading(false);
    }
      setInvoices([newInvoice, ...invoices]);
      setCurrentInvoiceId(newInvoice.id);
      setIsUploading(false);
      setShowUploadModal(false);
      
       // If it's a PDF, create a preview image
      if (isPdf) {
        renderPdfPreview(file);
      }

      // Add welcome message
      const welcomeMessage: Message = {
        id: Date.now().toString(),
        content: `I've processed the invoice "${file.name}". You can now ask me questions about this invoice.`,
        role: 'assistant',
        timestamp: new Date()
      };
      
      setTimeout(() => {
        setInvoices(prevInvoices => 
          prevInvoices.map(inv => 
            inv.id === newInvoice.id 
              ? { ...inv, messages: [...inv.messages, welcomeMessage] }
              : inv
          )
        );
      }, 1000);
    }, 2000);
  };
  const renderPdfPreview = async (file: File) => {
    const fileReader = new FileReader();
    fileReader.onload = (e: any) => {
      const typedArray = new Uint8Array(e.target.result);
  
      // Load the PDF using PDF.js
      pdfjsLib.getDocument(typedArray).promise.then((pdf) => {
        // Fetch the first page of the PDF
        pdf.getPage(1).then((page) => {
          const scale = 1.5;
          const viewport = page.getViewport({ scale });
  
          const canvas = document.createElement('canvas');
          const context = canvas.getContext('2d');
          if (context) {
            canvas.height = viewport.height;
            canvas.width = viewport.width;
  
            // Render the page onto the canvas
            page.render({
              canvasContext: context,
              viewport: viewport
            }).promise.then(() => {
              // Convert canvas to image and set preview
              const imgUrl = canvas.toDataURL();
              setInvoices(prevInvoices =>
                prevInvoices.map(inv =>
                  inv.id === currentInvoiceId
                    ? { ...inv, previewUrl: imgUrl }
                    : inv
                )
              );
            });
          }
        });
      });
    };
    fileReader.readAsArrayBuffer(file);
  };
  // Delete an invoice
  const handleDeleteInvoice = (id: string) => {
    const updatedInvoices = invoices.filter(inv => inv.id !== id);
    setInvoices(updatedInvoices);
    
    if (id === currentInvoiceId) {
      setCurrentInvoiceId(updatedInvoices[0]?.id || '');
    }
    
    // Revoke object URL to avoid memory leaks
    const invoiceToDelete = invoices.find(inv => inv.id === id);
    if (invoiceToDelete?.previewUrl) {
      URL.revokeObjectURL(invoiceToDelete.previewUrl);
    }
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isLoading || !currentInvoice) return;
    
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue.trim(),
      role: 'user',
      timestamp: new Date()
    };
    
    // Update invoice with user message
    const updatedInvoices = invoices.map(inv => {
      if (inv.id === currentInvoiceId) {
        return {
          ...inv,
          messages: [...inv.messages, userMessage]
        };
      }
      return inv;
    });
    
    setInvoices(updatedInvoices);
    setInputValue('');
    setIsLoading(true);
    
    // Simulate AI response after a delay
    setTimeout(async() => {
      const aiResponse: Message = {
        id: Date.now().toString(),
        content: await getAIResponse(inputValue),
        role: 'assistant',
        timestamp: new Date()
      };
      
      const finalInvoices = updatedInvoices.map(inv => {
        if (inv.id === currentInvoiceId) {
          return {
            ...inv,
            messages: [...inv.messages, aiResponse]
          };
        }
        return inv;
      });
      
      setInvoices(finalInvoices);
      setIsLoading(false);
    }, 1500);
  };

  // Simple AI response generator
  const getAIResponse = async (input: string): Promise<string> => {
    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: input })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.response || "No response from AI";
      
    } catch (error) {
      console.error("Error:", error);
      return "Error fetching response";
    }
  };

  return (
    <div className="flex h-screen bg-white text-gray-800">
      {/* Mobile sidebar toggle */}
      <button 
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-gray-100 rounded-md"
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
      >
        {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Sidebar */}
      <div className={`${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} 
        md:translate-x-0 transition-transform duration-300 ease-in-out
        fixed md:static inset-y-0 left-0 w-64 bg-gray-50 border-r border-gray-200 
        flex flex-col z-40`}>
        {/* App Logo */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center">
            <img 
              src="/supplier-logo.svg" 
              alt="SupplierGPT Logo" 
              className="h-10"
            />
            <span className="ml-2 text-xl font-bold">SupplierGPT</span>
          </div>
        </div>
        
        {/* Upload invoice button */}
        <div className="p-4">
          <button 
            onClick={() => setShowUploadModal(true)}
            className="w-full flex items-center gap-2 px-4 py-3 rounded-md bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          >
            <Upload size={16} />
            <span>Upload Invoice</span>
          </button>
        </div>
        
        {/* Invoices list */}
        <div className="flex-1 overflow-y-auto px-3 py-2">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-2">Your Invoices</h2>
          {invoices.length === 0 ? (
            <div className="text-center py-6 text-gray-500">
              <FileUp className="mx-auto mb-2" size={24} />
              <p>No invoices yet</p>
              <p className="text-xs mt-1">Upload an invoice to get started</p>
            </div>
          ) : (
            <ul className="space-y-1">
              {invoices.map(invoice => (
                <li key={invoice.id} className="relative group">
                  <button
                    onClick={() => setCurrentInvoiceId(invoice.id)}
                    className={`w-full text-left px-3 py-2 rounded-md flex items-center gap-2 truncate ${
                      currentInvoiceId === invoice.id 
                        ? 'bg-gray-200 text-gray-900' 
                        : 'hover:bg-gray-100 text-gray-700'
                    }`}
                  >
                    <span className="flex-shrink-0">
                      <File size={16} />
                    </span>
                    <span className="truncate">{invoice.name}</span>
                  </button>
                  <button 
                    onClick={() => handleDeleteInvoice(invoice.id)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 text-gray-500 hover:text-red-500 transition-opacity"
                  >
                    <Trash2 size={16} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        
        {/* App info */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center gap-2 px-3 py-2">
            <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center">
              <Bot size={16} />
            </div>
            <span className="font-medium">Invoice Assistant</span>
          </div>
          <p className="text-xs text-gray-500 mt-2 px-3">
            Upload invoices and ask questions to extract information quickly.
          </p>
        </div>
      </div>
      
      {/* Main content */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Chat area */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8">
          {!currentInvoice ? (
            <div className="h-full flex flex-col items-center justify-center">
              <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
                <FileUp size={32} className="text-gray-500" />
              </div>
              <h1 className="text-2xl font-semibold text-gray-800 mb-2">No invoice selected</h1>
              <p className="text-gray-500 text-center max-w-md">
                Upload an invoice or select one from the sidebar to start asking questions.
              </p>
              <button 
                onClick={() => setShowUploadModal(true)}
                className="mt-6 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Upload Invoice
              </button>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto">
              {currentInvoice.previewUrl && (
                <div className="mb-6 p-4 border border-gray-200 rounded-lg bg-gray-50">
                  <h2 className="font-medium text-gray-700 mb-2">Invoice Preview</h2>
                  <div className="aspect-[8.5/11] bg-white border border-gray-300 rounded overflow-hidden">
                    <img 
                      src={currentInvoice.previewUrl} 
                      alt={`Preview of ${currentInvoice.name}`}
                      className="w-full h-full object-contain"
                    />
                  </div>
                </div>
              )}
              
              {/* Messages */}
              {currentInvoice.messages.map((message) => (
                <div 
                  key={message.id} 
                  className={`mb-6 ${message.role === 'assistant' ? 'bg-gray-50 -mx-4 md:-mx-8 p-4 md:p-8 border-t border-b border-gray-100' : ''}`}
                >
                  <div className="flex items-start gap-4 max-w-3xl mx-auto">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      message.role === 'assistant' ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-700'
                    }`}>
                      {message.role === 'assistant' ? <Bot size={16} /> : <User size={16} />}
                    </div>
                    <div className="flex-1 prose">
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="mb-6 bg-gray-50 -mx-4 md:-mx-8 p-4 md:p-8 border-t border-b border-gray-100">
                  <div className="flex items-start gap-4 max-w-3xl mx-auto">
                    <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center flex-shrink-0">
                      <Bot size={16} />
                    </div>
                    <div className="flex-1">
                      <div className="flex space-x-2">
                        <div className="w-2 h-2 rounded-full bg-gray-300 animate-pulse"></div>
                        <div className="w-2 h-2 rounded-full bg-gray-300 animate-pulse delay-150"></div>
                        <div className="w-2 h-2 rounded-full bg-gray-300 animate-pulse delay-300"></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
        
        {/* Input area */}
        <div className="border-t border-gray-200 p-4 bg-white">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
            <div className="relative">
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                placeholder={currentInvoice ? "Ask a question about this invoice..." : "Upload an invoice to start..."}
                disabled={!currentInvoice}
                className="w-full border border-gray-300 rounded-lg py-3 pl-4 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none max-h-[200px] overflow-y-auto disabled:bg-gray-100 disabled:text-gray-400"
                rows={1}
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isLoading || !currentInvoice}
                className={`absolute right-3 bottom-3 p-1 rounded-md ${
                  inputValue.trim() && !isLoading && currentInvoice
                    ? 'text-blue-600 hover:bg-blue-50'
                    : 'text-gray-400'
                }`}
              >
                <Send size={20} />
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              {currentInvoice 
                ? "Ask questions like 'What's the total amount?' or 'Who is the vendor?'" 
                : "Upload an invoice to start asking questions"}
            </p>
          </form>
        </div>
      </div>
      
      {/* Upload modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h2 className="text-xl font-semibold mb-4">Upload Invoice</h2>
            <p className="text-gray-600 mb-4">
              Upload an invoice file (PDF, PNG, or JPG) to analyze and extract information.
            </p>
            
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-4">
              <FileUp className="mx-auto mb-2 text-gray-400" size={32} />
              <p className="text-sm text-gray-500 mb-4">Drag and drop your file here, or click to browse</p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={handleFileUpload}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                disabled={isUploading}
              >
                {isUploading ? 'Uploading...' : 'Select File'}
              </button>
            </div>
            
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowUploadModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                disabled={isUploading}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;