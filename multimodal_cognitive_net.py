# -*- coding: utf-8 -*-
"""
================================================================================
🌱 ARA Organic Cognitive Core: Multimodal Integration System (CognitiveExpansionNet)
================================================================================

This module implements a state-of-the-art multimodal deep learning architecture 
in PyTorch, integrating:
  1. Natural Language (Text Processing Pipeline via Pre-trained Transformer)
  2. Time-Series (Temporal Trend Extraction via LSTM)
  3. Sensor/Numerical Data (Feature Normalization and MLP Projection)
  
These sub-pipelines are dynamically fused with existing parsed data within the main 
orchestrator, CognitiveExpansionNet, supporting three selectable fusion strategies:
  - 'concat': Concatenation + Multi-Layer Perceptron (Baseline)
  - 'gated': Gated Multimodal Fusion (Learned attention gates over modalities)
  - 'attention': Multi-Head Cross-Attention Fusion (Contextual token interaction)
"""

import os
import sys
import io

# Force stdout/stderr to use UTF-8 encoding to prevent CP949 encoding crashes on Windows consoles
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Fallback for older python versions
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ---------------------------------------------------------
# 1. Dependency & Environment Check
# ---------------------------------------------------------
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from transformers import AutoTokenizer, AutoModel
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


# ==========================================================================
# PART A: Actual PyTorch Implementation (Runs if PyTorch is installed)
# ==========================================================================
if HAS_TORCH:
    
    # ---------------------------------------------------------
    # 1. Natural Language Text Pipeline
    # ---------------------------------------------------------
    class TextProcessingPipeline(nn.Module):
        """
        Extracts document semantic representation vectors using a pre-trained
        multilingual Transformer model. Handles offline fallbacks gracefully.
        """
        def __init__(self, model_name='bert-base-multilingual-cased', fallback_dim=768):
            super().__init__()
            self.model_name = model_name
            self.fallback_mode = False
            self.fallback_dim = fallback_dim
            
            if not HAS_TRANSFORMERS:
                print(f"[안내] transformers 패키지가 없어 시뮬레이션 텍스트 임베딩을 사용합니다.")
                self.fallback_mode = True
            else:
                try:
                    print(f"[로더] '{model_name}' 토크나이저 및 인코더 로드 중...")
                    self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                    self.encoder = AutoModel.from_pretrained(model_name)
                    print("[로더] 사전 학습된 트랜스포머 모델이 정상 로드되었습니다.")
                except Exception as e:
                    print(f"[경고] 허깅페이스 모델 로드 실패: {e}")
                    print("[안내] 오프라인 시뮬레이션 임베딩 레이어로 대체 작동합니다.")
                    self.fallback_mode = True
            
            if self.fallback_mode:
                # Fallback: simple hash mapping to a standard trainable Embedding layer
                self.vocab_lookup = {}
                self.embedding = nn.Embedding(2000, fallback_dim)
                
        def forward(self, text_list):
            device = next(self.parameters()).device
            
            if self.fallback_mode:
                # Convert text strings to pseudo-vocabulary indices
                indices = []
                for text in text_list:
                    if text not in self.vocab_lookup:
                        self.vocab_lookup[text] = len(self.vocab_lookup) % 2000
                    indices.append(self.vocab_lookup[text])
                
                idx_tensor = torch.tensor(indices, dtype=torch.long, device=device)
                return self.embedding(idx_tensor)
            else:
                # Normal forward pass through pre-trained BERT
                inputs = self.tokenizer(
                    text_list, 
                    padding=True, 
                    truncation=True, 
                    max_length=128,
                    return_tensors="pt"
                )
                # Send tokenized inputs to target device
                inputs = {k: v.to(device) for k, v in inputs.items()}
                outputs = self.encoder(**inputs)
                
                # [CLS] token embedding of shape (Batch, Hidden_Dim)
                document_vector = outputs.last_hidden_state[:, 0, :]
                return document_vector


    # ---------------------------------------------------------
    # 2. Time-Series/Sequential Data Pipeline
    # ---------------------------------------------------------
    class TimeSeriesPipeline(nn.Module):
        """
        Processes sequential inputs (e.g. stock, raw materials prices, system logs)
        using an LSTM to capture temporal dynamics and output a trend vector.
        """
        def __init__(self, input_features, hidden_dim):
            super().__init__()
            self.lstm = nn.LSTM(
                input_size=input_features, 
                hidden_size=hidden_dim, 
                batch_first=True
            )
            
        def forward(self, time_series_tensor):
            # Input tensor shape: (Batch, Sequence_Length, Features)
            lstm_out, (hidden_state, cell_state) = self.lstm(time_series_tensor)
            # Take the hidden state from the last layer (shape: Batch, Hidden_Dim)
            trend_vector = hidden_state[-1]
            return trend_vector


    # ---------------------------------------------------------
    # 3. Multidimensional Numerical/Sensor Data Pipeline
    # ---------------------------------------------------------
    class SensorDataPipeline(nn.Module):
        """
        Applies batch normalization to scale multidimensional features, 
        followed by a non-linear dense projection to extract sensor representations.
        """
        def __init__(self, num_features, hidden_dim):
            super().__init__()
            self.normalize = nn.BatchNorm1d(num_features)
            self.fc = nn.Linear(num_features, hidden_dim)
            
        def forward(self, sensor_tensor):
            # Handle single-sample batches (BatchNorm1d requires Batch > 1 during training)
            if self.training and sensor_tensor.size(0) == 1:
                norm_data = sensor_tensor # bypass normalization for single samples
            else:
                norm_data = self.normalize(sensor_tensor)
            
            hardware_vector = torch.relu(self.fc(norm_data))
            return hardware_vector


    # ---------------------------------------------------------
    # 4. Integrated Cognitive Expansion Network (CognitiveExpansionNet)
    # ---------------------------------------------------------
    class CognitiveExpansionNet(nn.Module):
        """
        The core neural orchestrator fusing Text, Time-Series, Sensor, and
        existing Parsed Data features with flexible fusion policies.
        """
        def __init__(self, 
                     parsed_dim=64,
                     ts_features=10,
                     ts_hidden_dim=64,
                     sensor_features=15,
                     sensor_hidden_dim=32,
                     text_model_name='bert-base-multilingual-cased',
                     text_dim=768,
                     fusion_strategy='gated', # 'concat', 'gated', 'attention'
                     output_dim=1,
                     num_heads=4):
            super().__init__()
            self.fusion_strategy = fusion_strategy.lower()
            
            # 1. Instantiate the modular sub-pipelines
            self.text_pipeline = TextProcessingPipeline(
                model_name=text_model_name, 
                fallback_dim=text_dim
            )
            self.time_series_pipeline = TimeSeriesPipeline(
                input_features=ts_features, 
                hidden_dim=ts_hidden_dim
            )
            self.sensor_pipeline = SensorDataPipeline(
                num_features=sensor_features, 
                hidden_dim=sensor_hidden_dim
            )
            
            # Dims
            self.parsed_dim = parsed_dim
            self.text_dim = text_dim
            self.ts_hidden_dim = ts_hidden_dim
            self.sensor_hidden_dim = sensor_hidden_dim
            
            # Projection dimension for unified fusion space (Gated / Attention)
            self.proj_dim = 128
            
            # Final output mapping MLP
            if self.fusion_strategy == 'concat':
                # Concat baseline connects all features directly
                total_raw_dim = parsed_dim + text_dim + ts_hidden_dim + sensor_hidden_dim
                self.fc_fuse = nn.Sequential(
                    nn.Linear(total_raw_dim, 256),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(256, output_dim)
                )
                
            elif self.fusion_strategy == 'gated':
                # Project all modalities into the same dimension (proj_dim)
                self.proj_parsed = nn.Linear(parsed_dim, self.proj_dim)
                self.proj_text = nn.Linear(text_dim, self.proj_dim)
                self.proj_ts = nn.Linear(ts_hidden_dim, self.proj_dim)
                self.proj_sensor = nn.Linear(sensor_hidden_dim, self.proj_dim)
                
                # Dynamic gate predictor
                self.gate_network = nn.Sequential(
                    nn.Linear(self.proj_dim * 4, 128),
                    nn.ReLU(),
                    nn.Linear(128, 4),
                    nn.Softmax(dim=1)
                )
                
                self.fc_fuse = nn.Sequential(
                    nn.Linear(self.proj_dim, 128),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(128, output_dim)
                )
                
            elif self.fusion_strategy == 'attention':
                # Project all modalities to a unified attention key-value size
                self.proj_parsed = nn.Linear(parsed_dim, self.proj_dim)
                self.proj_text = nn.Linear(text_dim, self.proj_dim)
                self.proj_ts = nn.Linear(ts_hidden_dim, self.proj_dim)
                self.proj_sensor = nn.Linear(sensor_hidden_dim, self.proj_dim)
                
                # Multi-head attention (Token interaction)
                self.mha = nn.MultiheadAttention(
                    embed_dim=self.proj_dim, 
                    num_heads=num_heads, 
                    batch_first=True
                )
                self.layernorm = nn.LayerNorm(self.proj_dim)
                
                self.fc_fuse = nn.Sequential(
                    nn.Linear(self.proj_dim, 128),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(128, output_dim)
                )
            else:
                raise ValueError(f"지원하지 않는 융합 전략입니다: {fusion_strategy}. ('concat', 'gated', 'attention' 중 선택)")

        def forward(self, parsed_data, local_documents, market_data, sensor_data):
            """
            Args:
                parsed_data (Tensor): (Batch, parsed_dim)
                local_documents (List[str]): Batch lists of text documents
                market_data (Tensor): (Batch, Seq_Len, ts_features)
                sensor_data (Tensor): (Batch, sensor_features)
            Returns:
                output (Tensor): predicted output task values
                extra (dict): gates, weights, or embeddings generated in-flight
            """
            # Forward passes through dedicated streams
            text_vector = self.text_pipeline(local_documents)
            trend_vector = self.time_series_pipeline(market_data)
            hardware_vector = self.sensor_pipeline(sensor_data)
            
            # --- Option 1: Concatenation Fusion ---
            if self.fusion_strategy == 'concat':
                combined_features = torch.cat(
                    (parsed_data, text_vector, trend_vector, hardware_vector), 
                    dim=1
                )
                output = self.fc_fuse(combined_features)
                return output, {"combined_features": combined_features}
                
            # --- Option 2: Gated Multimodal Fusion ---
            elif self.fusion_strategy == 'gated':
                v_parsed = torch.relu(self.proj_parsed(parsed_data))
                v_text = torch.relu(self.proj_text(text_vector))
                v_ts = torch.relu(self.proj_ts(trend_vector))
                v_sensor = torch.relu(self.proj_sensor(hardware_vector))
                
                # Predict dynamic importance score gates
                combined_proj = torch.cat((v_parsed, v_text, v_ts, v_sensor), dim=1)
                gates = self.gate_network(combined_proj) # (Batch, 4)
                
                # Fuse via weighted gate scores
                fused_vector = (
                    gates[:, 0:1] * v_parsed +
                    gates[:, 1:2] * v_text +
                    gates[:, 2:3] * v_ts +
                    gates[:, 3:4] * v_sensor
                )
                
                output = self.fc_fuse(fused_vector)
                return output, {"gates": gates, "fused_vector": fused_vector}
                
            # --- Option 3: Cross-Attention Fusion ---
            elif self.fusion_strategy == 'attention':
                v_parsed = torch.relu(self.proj_parsed(parsed_data)).unsqueeze(1) # (Batch, 1, proj_dim)
                v_text = torch.relu(self.proj_text(text_vector)).unsqueeze(1)     # (Batch, 1, proj_dim)
                v_ts = torch.relu(self.proj_ts(trend_vector)).unsqueeze(1)         # (Batch, 1, proj_dim)
                v_sensor = torch.relu(self.proj_sensor(hardware_vector)).unsqueeze(1) # (Batch, 1, proj_dim)
                
                # Stack modalities as structured sequence: (Batch, 4 Tokens, proj_dim)
                seq = torch.cat((v_parsed, v_text, v_ts, v_sensor), dim=1)
                
                # Self-Attention token representation updates
                attn_output, attn_weights = self.mha(seq, seq, seq)
                seq_fused = self.layernorm(seq + attn_output)
                
                # Pool along the sequence dim (mean pooling)
                fused_vector = seq_fused.mean(dim=1)
                
                output = self.fc_fuse(fused_vector)
                return output, {"attention_weights": attn_weights, "fused_vector": fused_vector}


# ==========================================================================
# MAIN EXECUTION CONTROLLER
# ==========================================================================
def main():
    print("\n" + "="*70)
    print("🌱 ARA Multimodal Cognitive Core Implementation Module Check")
    print("="*70 + "\n")
    
    if not HAS_TORCH:
        render_system_architecture_diagram()
        sys.exit(0)
        
    print("[시스템] PyTorch 디바이스 감지 중...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[디바이스] 가용 디바이스: {device}\n")
    
    # 1. Hyperparameters & Settings
    batch_size = 4
    seq_len = 10
    parsed_dim = 16
    ts_features = 5
    ts_hidden = 32
    sensor_features = 8
    sensor_hidden = 16
    text_dim = 768
    
    # Mock inputs
    mock_parsed = torch.randn(batch_size, parsed_dim).to(device)
    mock_ts = torch.randn(batch_size, seq_len, ts_features).to(device)
    mock_sensor = torch.randn(batch_size, sensor_features).to(device)
    mock_texts = [
        "Analysis of Brent crude oil prices and global supply disruptions.",
        "System metrics indicate high memory load and network bottleneck.",
        "Deep learning model optimization with mixed precision training.",
        "Eco-friendly autonomous vehicles sensor array calibration report."
    ]
    mock_targets = torch.randn(batch_size, 1).to(device)
    
    # Test each fusion strategy
    strategies = ['concat', 'gated', 'attention']
    
    for strategy in strategies:
        print("-"*60)
        print(f"🧬 [융합 테스트] 전략: {strategy.upper()}")
        print("-"*60)
        
        # Instantiate network
        net = CognitiveExpansionNet(
            parsed_dim=parsed_dim,
            ts_features=ts_features,
            ts_hidden_dim=ts_hidden,
            sensor_features=sensor_features,
            sensor_hidden_dim=sensor_hidden,
            text_dim=text_dim,
            fusion_strategy=strategy,
            output_dim=1
        ).to(device)
        
        # Optimizer & Loss
        criterion = nn.MSELoss()
        optimizer = optim.Adam(net.parameters(), lr=0.001)
        
        # Forward pass
        net.train()
        outputs, extra_info = net(mock_parsed, mock_texts, mock_ts, mock_sensor)
        
        loss = criterion(outputs, mock_targets)
        
        # Backward & Step
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Shapes & Outputs print
        print(f"  [출력] 예측 결과 텐서 셰이프 : {list(outputs.shape)}")
        print(f"  [오차] 배치 MSE 손실값 : {loss.item():.6f}")
        
        if strategy == 'concat':
            comb = extra_info['combined_features']
            print(f"  [상세] 병합 완료 특징 벡터 셰이프: {list(comb.shape)} "
                  f"(parsed {parsed_dim} + text {text_dim} + ts {ts_hidden} + sensor {sensor_hidden})")
                  
        elif strategy == 'gated':
            gates = extra_info['gates']
            print(f"  [상세] 모달리티 게이트 분포 (Batch x 4):\n{gates.detach().cpu().numpy()}")
            print(f"  [상세] 게이트 가중합 벡터 셰이프: {list(extra_info['fused_vector'].shape)}")
            
        elif strategy == 'attention':
            attn = extra_info['attention_weights']
            print(f"  [상세] 멀티헤드 어텐션 가중치 셰이프 (Batch x Tokens x Tokens): {list(attn.shape)}")
            print(f"  [상세] 셀프 어텐션 융합 벡터 셰이프: {list(extra_info['fused_vector'].shape)}")
            
        print("✔️ 테스트 완료. 역전파 및 가중치 업데이트 정상 작동.\n")
        
    print("="*70)
    print("🎉 모든 멀티모달 융합 전략 파이프라인 검증 성공!")
    print("="*70 + "\n")


def render_system_architecture_diagram():
    """ Renders a dynamic and beautiful console flow diagram explaining the architecture. """
    print("⚠️  컴퓨터에 PyTorch 환경이 구성되어 있지 않아 아키텍처 다이어그램을 출력합니다.")
    print("    본 모듈을 실제로 구동하려면 아래 명령어로 패키지를 설치하십시오:")
    print("    >> pip install torch transformers\n")
    
    diagram = """
          ┌──────────────────────────────────────────────────────────┐
          │         INPUT DATA SOURCES (멀티모달 다차원 입력)        │
          └─────────────────────────────┬────────────────────────────┘
                                        │
      ┌──────────────────┬──────────────┼───────────────┬──────────────────┐
      ▼                  ▼              ▼               ▼                  ▼
┌───────────┐    ┌──────────────┐ ┌───────────┐   ┌───────────┐      ┌───────────┐
│Parsed Data│    │Research Text │ │Time-Series│   │Sensor Data│      │... Others │
│(CSV/Logs) │    │(Papers/Logs) │ │(Financial)│   │(Hardware) │      │           │
└─────┬─────┘    └──────┬───────┘ └─────┬─────┘   └─────┬─────┘      └─────┬─────┘
      │                 │               │               │                  │
      │           (BERT Encoder)  (LSTM Stream)  (BatchNorm+FC)            │
      ▼                 ▼               ▼               ▼                  ▼
[1xParsed_Dim]    [1xText_Dim]     [1xTS_Dim]      [1xSensor_Dim]      [1xN_Dim]
 (e.g. 64)         (e.g. 768)       (e.g. 64)       (e.g. 32)
      │                 │               │               │                  │
      └─────────────────┼───────────────┼───────────────┘                  │
                        ▼               ▼                                  ▼
      ┌────────────────────────────────────────────────────────────────────┐
      │             FUSION STRATEGY ENGINE (설정 선택 가능)               │
      │                                                                    │
      │  [concat]    -> Concatenates streams directly into dense MLP       │
      │  [gated]     -> Dynamic soft-gating vector weight mapping          │
      │  [attention] -> Multi-Head Cross-Attention interaction (Tokens)    │
      └─────────────────────────────────┬──────────────────────────────────┘
                                        │
                                        ▼
                         ┌─────────────────────────────┐
                         │   Shared Projection Space   │
                         │      (Unified 256-Dim)      │
                         └──────────────┬──────────────┘
                                        │
                                        ▼
                         ┌─────────────────────────────┐
                         │      Dense Prediction       │
                         │      Regression/Class       │
                         └──────────────┬──────────────┘
                                        │
                                        ▼
                                 [Final Result]
    """
    print(diagram)


if __name__ == "__main__":
    main()
