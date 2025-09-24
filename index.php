<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GIMG2 - Web Control Panel</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; background-color: #f4f7f9; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: #fff; padding: 20px 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h1, h2 { color: #2c3e50; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }
        form { margin-bottom: 20px; } label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"], textarea, select { width: 100%; padding: 10px; margin-bottom: 15px; border-radius: 4px; border: 1px solid #ccc; box-sizing: border-box; }
        textarea { resize: vertical; min-height: 80px; }
        button { background-color: #27ae60; color: white; padding: 15px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 18px; font-weight: bold; transition: background-color 0.3s; width: 100%;}
        button:hover { background-color: #229954; }
        .output-box { background-color: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; font-family: "Courier New", Courier, monospace; max-height: 400px; overflow-y: auto; }
        .result { margin-top: 20px; padding: 20px; border-left: 5px solid #27ae60; background-color: #e9f7ef; border-radius: 5px; }
        .result a { color: #27ae60; font-weight: bold; font-size: 1.2em; text-decoration: none;}
    </style>
</head>
<body>
    <div class="container">
        <h1>GIMG2 - Automated Workflow</h1>
        
        <h2>Create Account & Generate Image</h2>
        <p>This will perform the entire process: create a new account, log in, and generate your image in a single, seamless operation.</p>
        
        <form method="post" action="" enctype="multipart/form-data">
            <label for="prompt">1. Enter Your Prompt:</label>
            <textarea id="prompt" name="prompt" required placeholder="A majestic lion on a grassy savannah, photorealistic..."></textarea>
            
            <label for="image_upload">2. (Optional) Upload a Reference Image:</label>
            <input type="file" id="image_upload" name="image_upload">
            
            <label for="ratio">3. Select Aspect Ratio:</label>
            <select id="ratio" name="ratio"><option>16:9</option><option selected>1:1</option><option>9:16</option></select>
            
            <label for="resolution">4. Select Resolution:</label>
            <select id="resolution" name="resolution"><option selected>1k</option><option>2k</option><option>4k</option></select>
            
            <label for="format">5. Select Download Format:</label>
            <select id="format" name="format"><option>png</option><option selected>jpg</option></select>
            
            <button type="submit" name="action" value="register-and-generate">Start Full Automation</button>
        </form>

        <?php
        if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_POST['action'])) {
            // (The real-time output PHP code is unchanged)
            if (ini_get('zlib.output_compression')) { ini_set('zlib.output_compression', 'Off'); }
            while (@ob_end_flush());
            ini_set('output_buffering', 'Off');
            
            set_time_limit(1000); 
            $action = $_POST['action'];
            
            $python_executable = 'python'; // Use 'python' or full path
            $command = escapeshellarg($python_executable) . ' ' . escapeshellarg(realpath('run_automation.py'));
            
            if ($action == 'register-and-generate') {
                $command .= ' register-and-generate';
                $command .= ' --prompt ' . escapeshellarg($_POST['prompt']);
                $command .= ' --ratio ' . escapeshellarg($_POST['ratio']);
                $command .= ' --resolution ' . escapeshellarg($_POST['resolution']);
                $command .= ' --format ' . escapeshellarg($_POST['format']);
                
                if (isset($_FILES['image_upload']) && $_FILES['image_upload']['error'] == 0) {
                    $upload_dir = realpath('uploads');
                    $uploaded_file = $upload_dir . '/' . basename($_FILES['image_upload']['name']);
                    if (move_uploaded_file($_FILES['image_upload']['tmp_name'], $uploaded_file)) {
                        $command .= ' --image-path ' . escapeshellarg($uploaded_file);
                    }
                }
            }

            echo '<h2>Execution Log</h2>';
            echo '<div class="output-box">';
            
            $handle = popen($command . ' 2>&1', 'r');
            $output_buffer = '';
            if ($handle) {
                while (!feof($handle)) {
                    $line = fgets($handle);
                    echo htmlspecialchars($line);
                    @flush(); @ob_flush();
                    $output_buffer .= $line;
                }
                pclose($handle);
            }
            
            echo '</div>';
            
            preg_match('/FINAL_PATH:(.*)/', $output_buffer, $matches);
            if (isset($matches[1])) {
                $raw_path = trim($matches[1]);
                $relative_path = str_replace(realpath(getcwd()), '', realpath($raw_path));
                $web_path = str_replace('\\', '/', $relative_path);
                
                echo '<div class="result">';
                echo '✅ <strong>Success!</strong> Your image has been generated.';
                echo '<p><a href="' . $web_path . '" download>Click here to download your image</a></p>';
                echo '</div>';
            }
        }
        ?>
    </div>
</body>
</html>