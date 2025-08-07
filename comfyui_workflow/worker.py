#!/usr/bin/env python3
"""
ComfyUI Workflow Worker for WAN2.2 I2V
Executes arbitrary JSON workflows via ComfyUI API
"""

import json
import requests
import time
import base64
import io
import os
from PIL import Image


class ComfyUIWorker:
    def __init__(self, server_url="http://localhost:8188", timeout=600):
        self.server_url = server_url
        self.timeout = timeout
        
    def upload_image(self, image_path, filename=None):
        """Upload image to ComfyUI server"""
        if filename is None:
            filename = os.path.basename(image_path)
            
        with open(image_path, 'rb') as f:
            files = {'image': (filename, f, 'image/png')}
            response = requests.post(f"{self.server_url}/upload/image", files=files)
            return response.json()
    
    def queue_workflow(self, workflow_json):
        """Queue a workflow for execution"""
        response = requests.post(f"{self.server_url}/prompt", json={"prompt": workflow_json})
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to queue workflow: {response.status_code} - {response.text}")
    
    def get_history(self, prompt_id):
        """Get execution history for a prompt"""
        response = requests.get(f"{self.server_url}/history/{prompt_id}")
        return response.json()
    
    def wait_for_completion(self, prompt_id, timeout=None):
        """Wait for workflow completion using polling"""
        if timeout is None:
            timeout = self.timeout
            
        return self._poll_for_completion(prompt_id, timeout)
    
    def _poll_for_completion(self, prompt_id, timeout):
        """Fallback polling method"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                history = self.get_history(prompt_id)
                if prompt_id in history:
                    status = history[prompt_id].get('status', {})
                    if status.get('completed', False):
                        return True
                    elif 'error' in status:
                        raise Exception(f"Workflow execution failed: {status['error']}")
                        
            except requests.RequestException as e:
                print(f"Error checking status: {e}")
                
            time.sleep(2)
            
        return False
    
    def get_output_images(self, prompt_id):
        """Get output images from completed workflow"""
        history = self.get_history(prompt_id)
        
        if prompt_id not in history:
            return []
            
        outputs = history[prompt_id].get('outputs', {})
        images = []
        
        for node_id, output in outputs.items():
            if 'images' in output:
                for image_info in output['images']:
                    filename = image_info['filename']
                    subfolder = image_info.get('subfolder', '')
                    
                    # Download the image
                    img_url = f"{self.server_url}/view"
                    params = {'filename': filename}
                    if subfolder:
                        params['subfolder'] = subfolder
                        
                    response = requests.get(img_url, params=params)
                    if response.status_code == 200:
                        images.append({
                            'filename': filename,
                            'data': response.content,
                            'node_id': node_id
                        })
                        
        return images
    
    def get_output_videos(self, prompt_id):
        """Get output videos from completed workflow"""
        history = self.get_history(prompt_id)
        
        if prompt_id not in history:
            return []
            
        outputs = history[prompt_id].get('outputs', {})
        videos = []
        
        for node_id, output in outputs.items():
            if 'videos' in output:
                for video_info in output['videos']:
                    filename = video_info['filename']
                    subfolder = video_info.get('subfolder', '')
                    
                    # Download the video
                    video_url = f"{self.server_url}/view"
                    params = {'filename': filename}
                    if subfolder:
                        params['subfolder'] = subfolder
                        
                    response = requests.get(video_url, params=params)
                    if response.status_code == 200:
                        videos.append({
                            'filename': filename,
                            'data': response.content,
                            'node_id': node_id
                        })
                        
        return videos
    
    def execute_workflow(self, workflow_json, save_outputs=True, output_dir="./output"):
        """Execute a complete workflow and return results"""
        print("Queuing workflow for execution...")
        
        # Queue the workflow
        result = self.queue_workflow(workflow_json)
        prompt_id = result['prompt_id']
        print(f"Workflow queued with ID: {prompt_id}")
        
        # Wait for completion
        print("Waiting for workflow completion...")
        success = self.wait_for_completion(prompt_id)
        
        if not success:
            raise Exception(f"Workflow execution timed out after {self.timeout} seconds")
            
        print("Workflow completed successfully!")
        
        # Get outputs
        images = self.get_output_images(prompt_id)
        videos = self.get_output_videos(prompt_id)
        
        results = {
            'prompt_id': prompt_id,
            'images': images,
            'videos': videos
        }
        
        # Save outputs if requested
        if save_outputs and (images or videos):
            os.makedirs(output_dir, exist_ok=True)
            
            for img in images:
                img_path = os.path.join(output_dir, f"{prompt_id}_{img['filename']}")
                with open(img_path, 'wb') as f:
                    f.write(img['data'])
                print(f"Saved image: {img_path}")
                
            for video in videos:
                video_path = os.path.join(output_dir, f"{prompt_id}_{video['filename']}")
                with open(video_path, 'wb') as f:
                    f.write(video['data'])
                print(f"Saved video: {video_path}")
        
        return results


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ComfyUI Workflow Worker')
    parser.add_argument('-w', '--workflow', required=True, help='Path to workflow JSON file')
    parser.add_argument('-s', '--start-image', help='Path to start image (for FLF workflows)')
    parser.add_argument('-e', '--end-image', help='Path to end image (for FLF workflows)')
    parser.add_argument('-p', '--positive-prompt', help='Positive prompt')
    parser.add_argument('-n', '--negative-prompt', help='Negative prompt')
    parser.add_argument('--width', type=int, default=640, help='Video width')
    parser.add_argument('--height', type=int, default=640, help='Video height')
    parser.add_argument('--length', type=int, default=81, help='Video length in frames')
    parser.add_argument('--server', default='http://localhost:8188', help='ComfyUI server URL')
    parser.add_argument('-o', '--output', default='./output', help='Output directory')
    
    args = parser.parse_args()
    
    # Initialize worker
    worker = ComfyUIWorker(args.server)
    
    # Load workflow
    with open(args.workflow, 'r') as f:
        workflow = json.load(f)
    
    # Upload images if provided
    if args.start_image:
        print(f"Uploading start image: {args.start_image}")
        worker.upload_image(args.start_image, "start.png")
        
    if args.end_image:
        print(f"Uploading end image: {args.end_image}")
        worker.upload_image(args.end_image, "end.png")
    
    # Update workflow parameters if provided
    if args.positive_prompt and '6' in workflow:
        workflow['6']['inputs']['text'] = args.positive_prompt
        
    if args.negative_prompt and '7' in workflow:
        workflow['7']['inputs']['text'] = args.negative_prompt
        
    if '67' in workflow:
        workflow['67']['inputs']['width'] = args.width
        workflow['67']['inputs']['height'] = args.height
        workflow['67']['inputs']['length'] = args.length
    
    # Execute workflow
    try:
        results = worker.execute_workflow(workflow, output_dir=args.output)
        print(f"Execution completed! Generated {len(results['images'])} images and {len(results['videos'])} videos.")
        
        if results['videos']:
            print("Generated videos:")
            for video in results['videos']:
                print(f"  - {video['filename']}")
                
    except Exception as e:
        print(f"Error executing workflow: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())