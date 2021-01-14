#!/bin/bash

root=$1

if [ -z $root ]; then
    echo "./cut.sh <root>, e.g. ./cut.sh Dataset"
    exit
fi

for speaker in chem chess dl eh hs; do
    mp4s=$root/$speaker/videos/*

    for mp4 in $mp4s; do
        id=$(basename $mp4 .mp4)
        dir=$root/$speaker/intervals/$id
        if [ -d $dir ]; then
            echo $dir is skipped as it seems already cut.
            continue
        fi
        echo Spliting $mp4 ...
        mkdir -p $dir
        ffmpeg -loglevel panic -i $mp4 -acodec copy -f segment -vcodec copy -reset_timestamps 1 -map 0 -segment_time 30 "$dir/cut-%d.mp4"
    done
done
