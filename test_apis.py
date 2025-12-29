"""
Test all visual APIs to diagnose issues.
"""

import asyncio
import httpx
import os
import socket
import json
from dotenv import load_dotenv

load_dotenv()

# Force IPv4 for DNS resolution
socket.setdefaulttimeout(30)


async def test_fal():
    """Test Fal.ai API."""
    print("\n=== FAL.AI TEST ===")
    key = os.getenv('FAL_API_KEY')
    if not key:
        print("❌ No FAL_API_KEY set")
        return
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # Submit to queue
            resp = await client.post(
                'https://queue.fal.run/fal-ai/flux/dev',
                headers={
                    'Authorization': f'Key {key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'prompt': 'A dark cinematic scene with dramatic lighting',
                    'image_size': 'portrait_16_9',
                    'num_images': 1
                }
            )
            print(f"Status: {resp.status_code}")
            data = resp.json()
            print(f"Response keys: {list(data.keys())}")
            
            # Check if queued
            if 'request_id' in data:
                request_id = data['request_id']
                response_url = data.get('response_url')  # Use the provided URL
                print(f"✅ Queued with ID: {request_id}")
                print(f"   Response URL: {response_url}")
                
                if response_url:
                    # Poll using the response_url directly
                    for i in range(30):
                        await asyncio.sleep(3)
                        
                        result_resp = await client.get(
                            response_url,
                            headers={'Authorization': f'Key {key}'}
                        )
                        
                        if result_resp.status_code == 200:
                            result = result_resp.json()
                            images = result.get('images', [])
                            if images:
                                print(f"✅ SUCCESS! Got {len(images)} image(s)")
                                print(f"  URL: {images[0].get('url', 'N/A')[:80]}...")
                                return
                        elif result_resp.status_code in [202, 400]:
                            # Still processing
                            print(f"  Poll {i+1}: still processing...")
                        else:
                            print(f"  Poll {i+1}: status {result_resp.status_code}")
                        
            elif 'images' in data:
                print(f"✅ Direct response with {len(data['images'])} images")
            elif 'error' in data:
                print(f"❌ Error: {data['error']}")
            else:
                print(f"❓ Unknown response: {json.dumps(data, indent=2)[:500]}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")


async def test_replicate():
    """Test Replicate API."""
    print("\n=== REPLICATE TEST ===")
    key = os.getenv('REPLICATE_API_TOKEN')
    if not key:
        print("❌ No REPLICATE_API_TOKEN set")
        return
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                'https://api.replicate.com/v1/predictions',
                headers={
                    'Authorization': f'Bearer {key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'version': '39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b',
                    'input': {
                        'prompt': 'A dark cinematic scene',
                        'width': 576,
                        'height': 1024,
                        'num_outputs': 1
                    }
                }
            )
            print(f"Status: {resp.status_code}")
            
            if resp.status_code == 429:
                print("⚠️ Rate limited (429) - wait 60 seconds between calls")
                return
            elif resp.status_code == 402:
                print("❌ Payment required - credits may be exhausted")
                return
            
            data = resp.json()
            print(f"Response keys: {list(data.keys())}")
            
            if 'urls' in data:
                pred_url = data['urls'].get('get')
                print(f"✅ Prediction started: {data.get('id')}")
                
                # Poll for result
                for i in range(30):
                    await asyncio.sleep(2)
                    status_resp = await client.get(
                        pred_url,
                        headers={'Authorization': f'Bearer {key}'}
                    )
                    status_data = status_resp.json()
                    status = status_data.get('status')
                    print(f"  Poll {i+1}: {status}")
                    
                    if status == 'succeeded':
                        output = status_data.get('output', [])
                        print(f"✅ SUCCESS! Got output: {output[0][:80] if output else 'N/A'}...")
                        return
                    elif status == 'failed':
                        print(f"❌ Failed: {status_data.get('error')}")
                        return
            else:
                print(f"❓ Response: {json.dumps(data, indent=2)[:500]}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")


async def test_runway():
    """Test Runway ML API."""
    print("\n=== RUNWAY ML TEST ===")
    key = os.getenv('RUNWAYML_API_KEY')
    if not key:
        print("❌ No RUNWAYML_API_KEY set")
        return
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # Test text_to_image with gen4_image model
            resp = await client.post(
                'https://api.dev.runwayml.com/v1/text_to_image',
                headers={
                    'Authorization': f'Bearer {key}',
                    'X-Runway-Version': '2024-11-06',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'gen4_image',
                    'promptText': 'A dark cinematic scene with dramatic lighting',
                    'ratio': '720:1280'  # Portrait
                }
            )
            print(f"Status: {resp.status_code}")
            
            if resp.status_code == 401:
                print("❌ Authentication failed (401)")
                try:
                    error_data = resp.json()
                    print(f"  Error: {error_data}")
                except:
                    print(f"  Raw: {resp.text[:200]}")
                return
            elif resp.status_code != 200:
                print(f"❌ Error: {resp.text[:300]}")
                return
            
            data = resp.json()
            task_id = data.get('id')
            print(f"✅ Task created: {task_id}")
            
            # Poll for result
            for i in range(30):
                await asyncio.sleep(3)
                status_resp = await client.get(
                    f'https://api.dev.runwayml.com/v1/tasks/{task_id}',
                    headers={
                        'Authorization': f'Bearer {key}',
                        'X-Runway-Version': '2024-11-06'
                    }
                )
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    status = status_data.get('status', '')
                    print(f"  Poll {i+1}: {status}")
                    
                    if status == 'SUCCEEDED':
                        output = status_data.get('output', [])
                        if output:
                            print(f"✅ SUCCESS! Image URL: {output[0][:80]}...")
                        return
                    elif status == 'FAILED':
                        print(f"❌ Failed: {status_data.get('failure', 'Unknown')}")
                        return
                
    except Exception as e:
        print(f"❌ Exception: {e}")


async def test_stability():
    """Test Stability AI API."""
    print("\n=== STABILITY AI TEST ===")
    key = os.getenv('STABILITY_API_KEY')
    if not key:
        print("❌ No STABILITY_API_KEY set")
        return
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                'https://api.stability.ai/v2beta/stable-image/generate/core',
                headers={
                    'Authorization': f'Bearer {key}',
                    'Accept': 'application/json'  # Get JSON response with URL
                },
                files={'none': ('', '')},
                data={
                    'prompt': 'A dark cinematic scene with dramatic lighting',
                    'aspect_ratio': '9:16',
                    'output_format': 'png'
                }
            )
            print(f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                if 'image' in data:
                    print(f"✅ SUCCESS! Got base64 image")
                elif 'finish_reason' in data:
                    print(f"✅ SUCCESS! Finish reason: {data['finish_reason']}")
                else:
                    print(f"Response keys: {list(data.keys())}")
            else:
                print(f"❌ Error: {resp.text[:300]}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")


async def test_kie():
    """Test Kie AI API."""
    print("\n=== KIE AI TEST ===")
    key = os.getenv('KIE_API_KEY') or os.getenv('KIE_AI_API_KEY')
    if not key:
        print("❌ No KIE_API_KEY set")
        return
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # Use Flux Kontext API
            resp = await client.post(
                'https://api.kie.ai/api/v1/flux/kontext/generate',
                headers={
                    'Authorization': f'Bearer {key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'prompt': 'A dark cinematic scene with dramatic lighting',
                    'aspectRatio': '9:16',
                    'model': 'flux-kontext-pro',
                    'outputFormat': 'png'
                }
            )
            print(f"Status: {resp.status_code}")
            
            if resp.status_code != 200:
                print(f"❌ Error: {resp.text[:300]}")
                return
            
            data = resp.json()
            
            if data.get('code') != 200:
                print(f"❌ API Error: {data.get('msg', 'Unknown')}")
                return
            
            task_id = data.get('data', {}).get('taskId')
            print(f"✅ Task created: {task_id}")
            
            # Poll for result
            for i in range(30):
                await asyncio.sleep(3)
                status_resp = await client.get(
                    f'https://api.kie.ai/api/v1/flux/kontext/record-info?taskId={task_id}',
                    headers={'Authorization': f'Bearer {key}'}
                )
                
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    if status_data.get('code') == 200:
                        info = status_data.get('data', {})
                        success_flag = info.get('successFlag')
                        print(f"  Poll {i+1}: flag={success_flag}")
                        
                        if success_flag == 1:
                            result = info.get('response', {})
                            img_url = result.get('resultImageUrl', '')
                            print(f"✅ SUCCESS! Image URL: {img_url[:80]}...")
                            return
                        elif success_flag in [2, 3]:
                            print(f"❌ Failed: {info.get('errorMessage', 'Unknown')}")
                            return
                
    except httpx.ConnectError as e:
        print(f"❌ Connection error (DNS/Network): {e}")
    except Exception as e:
        print(f"❌ Exception: {e}")


async def test_leonardo():
    """Test Leonardo AI API."""
    print("\n=== LEONARDO AI TEST ===")
    key = os.getenv('LEONARDO_API_KEY')
    if not key or 'YOUR_' in key:
        print("❌ No valid LEONARDO_API_KEY set")
        print("  Get your key from: https://cloud.leonardo.ai/")
        return
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                'https://cloud.leonardo.ai/api/rest/v1/generations',
                headers={
                    'Authorization': f'Bearer {key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'prompt': 'A dark cinematic scene with dramatic lighting',
                    'modelId': 'aa77f04e-3eec-4034-9c07-d0f619684628',  # Leonardo Kino XL
                    'width': 576,
                    'height': 1024,
                    'num_images': 1
                }
            )
            print(f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                gen_id = data.get('sdGenerationJob', {}).get('generationId')
                print(f"✅ Generation started: {gen_id}")
                
                # Poll for completion
                for i in range(30):
                    await asyncio.sleep(3)
                    status_resp = await client.get(
                        f'https://cloud.leonardo.ai/api/rest/v1/generations/{gen_id}',
                        headers={'Authorization': f'Bearer {key}'}
                    )
                    if status_resp.status_code == 200:
                        status_data = status_resp.json()
                        images = status_data.get('generations_by_pk', {}).get('generated_images', [])
                        status = status_data.get('generations_by_pk', {}).get('status')
                        print(f"  Poll {i+1}: status={status}, images={len(images)}")
                        if images and images[0].get('url'):
                            print(f"✅ SUCCESS! Image URL: {images[0]['url'][:80]}...")
                            return
                print("❌ Timeout waiting for generation")
            else:
                print(f"❌ Error: {resp.text[:300]}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")


async def main():
    print("=" * 60)
    print("VISUAL API DIAGNOSTICS")
    print("=" * 60)
    
    # Test each API
    await test_stability()  # Most reliable
    await test_fal()
    await test_replicate()
    await test_runway()
    await test_kie()
    await test_leonardo()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
