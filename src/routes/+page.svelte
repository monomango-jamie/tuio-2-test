<script lang="ts">
	import { useSocket } from '@hardingjam/svelte-socket';
	import { appLoadingStatus } from '$lib/modules/AppLoader.svelte';
	import { fade } from 'svelte/transition';
	import { onMount } from 'svelte';

	const svelteSocket = useSocket();
	
	let videoElement: HTMLVideoElement;

	let touchStart = { x: 0, y: 0 };
	let targetElement: EventTarget | null = null;
	let focussedApp = $state<string | null>(null);
	let videoPlayed = $state(false);
	let isFadingIn = $state(true);
	let isFadingOut = $state(false);

	function handleTouchStart(e: TouchEvent) {
		e.preventDefault();
		touchStart = { x: e.touches[0].clientX, y: e.touches[0].clientY };
		targetElement = e.target;
	}

	function handleTouchEnd(e: TouchEvent) {
		e.preventDefault();
		if (targetElement && targetElement instanceof HTMLElement) {
			const dx = e.changedTouches[0].clientX - touchStart.x;
			const dy = e.changedTouches[0].clientY - touchStart.y;
			if (Math.sqrt(dx * dx + dy * dy) <= 150) {
				targetElement.click();
			}
		}
		targetElement = null;
	}

	function handleTapApp(appKey: string, e: MouseEvent) {
		e.stopPropagation();
		if (focussedApp === appKey) {
			// Second tap - start the app
			startApp(appKey);
			focussedApp = null;
		} else {
			// First tap - set focus
			focussedApp = appKey;
		}
	}



	async function startApp(appKey: string) {
		try {
			console.log(appKey);
			isFadingOut = true;

			// Wait for fade-to-black animation to complete before navigating
			await new Promise((resolve) => setTimeout(resolve, 500));

			appLoadingStatus.isLoading = true;

			svelteSocket.sendMessage(
				JSON.stringify({
					address: appKey,
					message: ['']
				})
			);

			const handleVisibility = () => {
				appLoadingStatus.isLoading = false;
				isFadingOut = false;
			};

			document.addEventListener('visibilitychange', handleVisibility);
		} catch (e) {
			console.error('Request failed:', e);
			alert('Failed to connect to controller');
			appLoadingStatus.isLoading = false;
			isFadingOut = false;
		}
	}

	type AppCard = {
		appKey: string;
		title: string;
		description: string;
		icon: string;
		image: string;
	};

	const apps: AppCard[] = [
		{
			appKey: '/ue1',
			title: 'Architact',
			description: 'Immerse into tactile digital twins of any 3D environment with Architact.',
			icon: '/icons/icon-architact.svg',
			image: '/architact.png'
		},
		{
			appKey: '/web1',
			title: 'Energy System Simulator',
			description: 'Explain complex data systems to clients with our tactile Data Visualisation Network.',
			icon: '/icons/icon-eef.svg',
			image: '/eef.png'
		},
		{
			appKey: '/ue2',
			title: 'Car Configurator',
			description: 'Visualize any product portfolio with our interactive Configurator.',
			icon: '/icons/icon-bmw.svg',
			image: '/bmw.png'
		}
	];

	onMount(() => {
		// Fade in from black after a short delay
		setTimeout(() => {
			isFadingIn = false;
		}, 100);

		// Autoplay background video
		if (videoElement) {
			videoElement
				.play()
				.then(() => {
					videoPlayed = true;
				})
				.catch((error) => {
					console.log('Video autoplay blocked, will play on user interaction:', error);
				});
		}


		document.addEventListener('visibilitychange', () => {
			if (document.visibilityState === 'visible') {
				isFadingOut = false;
				isFadingIn = true;
				setTimeout(() => {
					isFadingIn = false;
				}, 100);

						// Restart the video when page becomes visible
		if (videoElement) {
			videoElement.play().catch((error) => {
				console.log('Video restart failed:', error);
			});
		}
			}
		});
	});
</script>

<svelte:head>
	<link rel="preload" href="/bg-video.mp4" as="video" />
</svelte:head>
<svelte:body ontouchstart={handleTouchStart} ontouchend={handleTouchEnd} onclick={() => focussedApp = null} />

<main class="relative h-screen w-screen overflow-hidden">
	<!-- Background Video -->
	<video
		bind:this={videoElement}
		autoplay
		loop
		muted
		playsinline
		preload="auto"
		class="fixed inset-0 h-full w-full object-cover -z-10"
	>
		<source src="/bg-video.mp4" type="video/mp4" />
	</video>
	
	<!-- Logo -->
	<img
		src="/immersive-instruments-logo.svg"
		alt="Immersive Instruments Logo"
		class="absolute top-14 right-14 h-[76px] w-auto"
	/>

	<!-- Fade In/Out Overlay -->
	{#if isFadingIn}
		<div out:fade={{duration: 500}} class="absolute inset-0 z-[500] bg-black"></div>
	{/if}
	{#if isFadingOut || appLoadingStatus.isLoading}
		<div in:fade={{duration: 500}} class="absolute inset-0 z-[500] bg-black"></div>
	{/if}

	<!-- Cards Container -->
	<div class="flex h-full items-center justify-center gap-[80px] px-12 py-24">
		{#each apps as app (app.appKey)}
		<button class="flex flex-col gap-8 w-[600px] relative justify-center items-center"
							onclick={(e) => handleTapApp(app.appKey, e)}
>
			<div class="relative w-full h-[756px] flex-col items-center justify-center">
				<div class='w-[600px] backdrop-blur-sm z-0 rounded-[48px] absolute opacity-0 transition-opacity duration-300 h-[776px]' class:opacity-100={focussedApp !== app.appKey}></div>

				<div class='w-[600px] bg-white z-0 rounded-[48px] absolute opacity-0 transition-opacity duration-300 h-[776px]' class:opacity-100={focussedApp === app.appKey}></div>
				<div
					class="group relative z-10 flex h-[584px] w-[592px] flex-col overflow-hidden rounded-[44px] z-[200] mt-[4px] ml-[4px]"
				>
				<img
					src={app.image}
					alt={app.title}
					class="absolute inset-0 h-full w-full object-cover z-10"
				/>

				<img src={app.icon} alt={app.title} class="absolute top-[4px] right-[4px] z-10 h-20 w-20" />

				<!-- Play icon - shown when app is focused -->
				{#if focussedApp === app.appKey}

					<img in:fade={{duration: 300}} out:fade={{duration: 300}} src="/play-icon.svg" alt="Play" class="absolute top-1/2 left-1/2 z-20 -translate-x-1/2 -translate-y-1/2 h-[90px] w-[80px]" />
				{/if}

				<h2
					class="z-10 p-8 text-left text-[48px] leading-none font-bold text-[#fafafa]"
					style="font-family: 'Space Grotesk', sans-serif;"
				>
					{app.title}
				</h2>
				
			</div>
			{#if app.description}
				{@const words = app.description.split(' ')}
				<p class="relative z-[100] w-[527px] text-left text-[30px] leading-[45px] font-light justify-self-center pt-6 transition-colors duration-300" class:text-white={focussedApp !== app.appKey} class:text-black={focussedApp === app.appKey}>
					<strong class="font-bold">{words[0]}</strong> {words.slice(1).join(' ')}
				</p>
			{/if}
		</div>
		</button>
		{/each}
	</div>
</main>
